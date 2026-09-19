"""Entrenador de modelos de calibración de probabilidades faciales.

Justificación (PDF Sección 7):
  - Modelo por defecto: Regresión Logística (C=1.0, class_weight='balanced')
    Justificación: Interpretabilidad, rendimiento con pocos datos, probabilidad
    calibrada por naturaleza (sigmoid).
  - Alternativa: RandomForest + Isotonic Calibration
    Solo cuando hay >1000 registros históricos (necesita más datos para
    generalizar sin overfitting).
  - Métricas: accuracy, precision, recall, F1, FAR, FRR, matriz de confusión.

Entrenamiento: script CLI (python -m app.ml.train), NO endpoint HTTP.
  Justificación (PDF Sección 10): El entrenamiento es un proceso batch,
  no una operación en línea. Se ejecuta periódicamente cuando hay suficientes
  registros en ml_training_records.
"""
from __future__ import annotations
import os
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

# Umbral para decidir modelo (PDF Sección 7)
MIN_RECORDS_FOR_RF = 1000


class FaceTrainer:
    """Entrenador de modelos de calibración de probabilidades.

    Flujo (PDF Sección 7):
      1. Recolección: ml_training_records con similitud, distancia,
         calidad_imagen, iluminacion, resultado_real.
      2. Selección: LogReg si <1000 registros, RF+Isotonic si >1000.
      3. Entrenamiento con train/test split 80/20, stratified.
      4. Evaluación con métricas completas.
      5. Guardado como .joblib.
    """

    def __init__(self):
        self.base_model = None
        self.calibrated_model = None
        self.model_type = None

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Entrena el modelo seleccionando automáticamente la arquitectura.

        Args:
            X: Array de features [similitud, distancia, calidad_imagen, iluminacion]
            y: Array de labels (0=negativo, 1=positivo)

        Returns:
            Diccionario con métricas de evaluación.
        """
        n_records = len(X)
        n_positive = int(y.sum())
        n_negative = n_records - n_positive

        # Selección automática del modelo (PDF Sección 7)
        if n_records > MIN_RECORDS_FOR_RF:
            self._train_random_forest(X, y)
        else:
            self._train_logistic_regression(X, y)

        # Evaluación
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if n_positive >= 2 else None
        )

        y_pred = self.calibrated_model.predict(X_test)
        y_prob = self.calibrated_model.predict_proba(X_test)[:, 1]

        # Métricas (PDF Sección 7)
        metrics = self._compute_metrics(y_test, y_pred, y_prob)

        # FAR y FRR (PDF Sección 7)
        metrics["far"], metrics["frr"] = self._compute_far_frr(y_test, y_pred)
        metrics["n_records"] = n_records
        metrics["n_positive"] = n_positive
        metrics["n_negative"] = n_negative
        metrics["model_type"] = self.model_type

        logger.info(
            f"Model trained: {self.model_type} | "
            f"accuracy={metrics['accuracy']:.4f} | "
            f"FAR={metrics['far']:.4f} | FRR={metrics['frr']:.4f}"
        )

        return metrics

    def _train_logistic_regression(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entrena Regresión Logística con calibración (PDF Sección 7).

        LogisticRegression(C=1.0, class_weight='balanced'):
          - C=1.0: regularización por defecto (L2)
          - class_weight='balanced': compensa desbalance de clases
          - max_iter=1000: convergencia garantizada
        """
        self.model_type = "LogisticRegression"

        self.base_model = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )

        # Calibración isotónica para probabilidades precisas
        cv_folds = min(5, len(X) // 2) if len(X) >= 4 else 2
        self.calibrated_model = CalibratedClassifierCV(
            self.base_model, method="isotonic", cv=cv_folds
        )
        self.calibrated_model.fit(X, y)

        logger.info(f"LogReg trained: C=1.0, class_weight=balanced, cv={cv_folds}")

    def _train_random_forest(self, X: np.ndarray, y: np.ndarray) -> None:
        """Entrena RandomForest + Isotonic Calibration (solo si >1000 registros).

        RandomForestClassifier(n=100, depth=10):
          - n_estimators=100: balance entre sesgo y varianza
          - max_depth=10: limita profundidad para evitar overfitting
        """
        self.model_type = "RandomForest+Isotonic"

        self.base_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
        )

        cv_folds = min(5, len(X) // 2) if len(X) >= 4 else 2
        self.calibrated_model = CalibratedClassifierCV(
            self.base_model, method="isotonic", cv=cv_folds
        )
        self.calibrated_model.fit(X, y)

        logger.info(f"RF+Isotonic trained: n=100, depth=10, cv={cv_folds}")

    def _compute_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray
    ) -> dict:
        """Computa métricas completas (PDF Sección 7)."""
        tp = int(((y_pred == 1) & (y_true == 1)).sum())
        tn = int(((y_pred == 0) & (y_true == 0)).sum())
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())

        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
        }

    @staticmethod
    def _compute_far_frr(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
        """Calcula FAR (False Acceptance Rate) y FRR (False Rejection Rate).

        FAR = FP / (FP + TN)  → falsos aceptados / total negativos
        FRR = FN / (FN + TP)  → falsos rechazados / total positivos
        """
        fp = int(((y_pred == 1) & (y_true == 0)).sum())
        fn = int(((y_pred == 0) & (y_true == 1)).sum())
        tn = int(((y_pred == 0) & (y_true == 0)).sum())
        tp = int(((y_pred == 1) & (y_true == 1)).sum())

        far = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
        frr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0
        return far, frr

    def save(self, path: str = None) -> None:
        """Guarda el modelo calibrado como .joblib."""
        path = path or settings.ML_MODEL_PATH
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump(self.calibrated_model, path)
        logger.info(f"Calibrated model saved to {path}")

    def load(self, path: str = None) -> None:
        """Carga un modelo calibrado desde .joblib."""
        path = path or settings.ML_MODEL_PATH
        self.calibrated_model = joblib.load(path)
        self.model_type = type(self.calibrated_model).__name__
        logger.info(f"Calibrated model loaded from {path}")
