"""Entrenador de modelo de calibracion de probabilidades faciales.

Modelo: Regresion Logistica (C=0.5, class_weight='balanced')
  Interpretabilidad, rendimiento con pocos datos, probabilidad
  calibrada por naturaleza (sigmoid).
  Calibracion Isotonic para mejorar estimaciones de probabilidad.

Metricas: accuracy, precision, recall, F1, FAR, FRR, matriz de confusion.
Evaluacion: Stratified K-Fold Cross-Validation (metricas honestas).
"""
from __future__ import annotations
import os
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class FaceTrainer:
    def __init__(self):
        self.base_model = None
        self.calibrated_model = None
        self.model_type = None
        self.umbral_decision = settings.UMBRAL_DECISION

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        n_records = len(X)
        n_positive = int(y.sum())
        n_negative = n_records - n_positive
        unique_classes = len(np.unique(y))

        if unique_classes < 2:
            self.model_type = "Constant"
            from sklearn.dummy import DummyClassifier
            self.base_model = DummyClassifier(strategy="most_frequent")
            self.base_model.fit(X, y)
            self.calibrated_model = self.base_model
            logger.warning(f"Single class dataset ({n_positive} pos, {n_negative} neg). Using constant model.")
            return {
                "accuracy": 1.0 if n_positive > n_negative else 0.0,
                "precision": 1.0 if n_positive > n_negative else 0.0,
                "recall": 1.0,
                "f1_score": 1.0 if n_positive > n_negative else 0.0,
                "confusion_matrix": [[n_positive, 0], [0, n_negative]] if n_positive > n_negative else [[0, 0], [0, n_records]],
                "true_positives": n_positive if n_positive > n_negative else 0,
                "true_negatives": n_negative if n_negative > n_positive else 0,
                "false_positives": 0,
                "false_negatives": 0,
                "far": 0.0,
                "frr": 0.0,
                "n_records": n_records,
                "n_positive": n_positive,
                "n_negative": n_negative,
                "model_type": "Constant (single class)",
                "warning": f"Solo hay {n_positive} registros positivos. Confirma registros como Incorrecto para crear datos negativos.",
            }

        min_class = min(n_positive, n_negative)

        # --- PCA: reducir 512 dims a los mas relevantes (anti-overfitting) ---
        n_features = X.shape[1] if X.ndim > 1 else 1
        use_pca = n_features >= 100 and n_records >= 30
        if use_pca:
            from sklearn.decomposition import PCA
            max_components = min(64, n_records - 2, min_class * 2)
            pca = PCA(n_components=max_components, random_state=42)
            X = pca.fit_transform(X)
            explained = round(float(sum(pca.explained_variance_ratio_)) * 100, 1)
            logger.info(f"PCA: {n_features}d -> {X.shape[1]}d ({explained}% varianza explicada)")

        # --- Stratified K-Fold CV como evaluacion principal ---
        n_splits = min(5, min_class) if min_class >= 2 else 2
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        # C bajo = regularization fuerte. Para 512 dims, C=0.01 es necesario.
        C_val = getattr(self, "_C", 0.01)
        self.model_type = f"LogReg+CV+PCA({X.shape[1]}d)" if use_pca else "LogReg+CV"

        lr_for_cv = LogisticRegression(
            C=C_val, penalty="l2", solver="lbfgs",
            class_weight="balanced", max_iter=2000, random_state=42,
        )

        # --- CV: metricas honestas ---
        cv_acc = cross_val_score(lr_for_cv, X, y, cv=cv, scoring="accuracy")
        cv_prec = cross_val_score(lr_for_cv, X, y, cv=cv, scoring="precision_weighted")
        cv_rec = cross_val_score(lr_for_cv, X, y, cv=cv, scoring="recall_weighted")
        cv_f1 = cross_val_score(lr_for_cv, X, y, cv=cv, scoring="f1_weighted")

        cv_accuracy = round(float(cv_acc.mean()), 4)
        cv_precision = round(float(cv_prec.mean()), 4)
        cv_recall = round(float(cv_rec.mean()), 4)
        cv_f1_val = round(float(cv_f1.mean()), 4)
        cv_std = round(float(cv_acc.std()), 4)

        # --- Matriz de confusion CV (agregada de todos los folds) ---
        cv_cm = np.zeros((2, 2), dtype=int)
        for train_idx, test_idx in cv.split(X, y):
            X_tr, X_te = X[train_idx], X[test_idx]
            y_tr, y_te = y[train_idx], y[test_idx]
            lr_fold = LogisticRegression(
                C=C_val, penalty="l2", solver="lbfgs",
                class_weight="balanced", max_iter=2000, random_state=42,
            )
            lr_fold.fit(X_tr, y_tr)
            y_pred_cv = lr_fold.predict(X_te)
            cv_cm += confusion_matrix(y_te, y_pred_cv, labels=[0, 1])

        cv_tn = int(cv_cm[0, 0])
        cv_fp = int(cv_cm[0, 1])
        cv_fn = int(cv_cm[1, 0])
        cv_tp = int(cv_cm[1, 1])

        # --- Entrenar modelo FINAL con todos los datos (para produccion) ---
        self._train_logistic_regression(X, y, use_pca=use_pca, pca=pca if use_pca else None)

        # Curva FAR/FRR
        y_prob = self.calibrated_model.predict_proba(X)[:, 1]
        eval_y = np.asarray(y)
        curva = self._curva_far_frr(y_prob, eval_y)
        # Umbral orientado a la EXPERIENCIA DEL USUARIO: exige que el FRR no pase de
        # 0.20 (rescatar >=80% de los humanos reales atrapados como IA) y, dentro de
        # esos umbrales, elige el de MENOR FAR. Si ninguno logra FRR<=0.20, toma el de
        # menor FRR posible. Baja el umbral -> acepta humanos con mas facilidad.
        FRR_MAX = 0.20
        candidatos = [c for c in curva if c["frr"] <= FRR_MAX]
        if candidatos:
            recomendado = min(candidatos, key=lambda c: (c["far"], c["umbral"]))
        else:
            recomendado = min(curva, key=lambda c: (c["frr"], c["far"], c["umbral"]))
        self.umbral_decision = recomendado["umbral"]

        # --- Deteccion de overfitting ---
        train_y_pred = (y_prob >= self.umbral_decision).astype(int)
        train_acc = round(float(accuracy_score(eval_y, train_y_pred)), 4)
        brecha = round(train_acc - cv_accuracy, 4)

        overfitting = False
        overfitting_msg = ""
        if train_acc >= 0.999 and cv_accuracy < 0.95:
            overfitting = True
            overfitting_msg = (
                f"Train={train_acc:.0%} pero CV={cv_accuracy:.0%} (brecha {brecha:.0%}). "
                "El modelo memoriza los datos y no generaliza."
            )
        elif cv_accuracy >= 0.98 and n_records < 2000:
            overfitting = True
            overfitting_msg = (
                f"CV={cv_accuracy:.0%} con {n_records} registros. "
                "Con tan pocos datos el modelo puede no funcionar bien en el mundo real. "
                "Necesitas 2000+ muestras variadas (distinta iluminacion, fondos, "
                "angulos, expresiones, lentes, gorras, IA de distintos motores)."
            )
        elif cv_accuracy >= 0.999:
            overfitting = True
            overfitting_msg = (
                f"CV={cv_accuracy:.0%} con {n_records} registros: metricas perfectas "
                "sobre este dataset especifico. Agrega imagenes dificiles (IA de alta "
                "calidad, fotos con mala luz) para que el modelo aprenda a diferenciar "
                "mejor."
            )

        evaluacion = f"stratified {n_splits}-fold CV ({n_records} registros)"
        metricas_fiables = n_records >= 50 and min_class >= 15

        metrics = {
            "accuracy": cv_accuracy,
            "precision": cv_precision,
            "recall": cv_recall,
            "f1_score": cv_f1_val,
            "train_accuracy": train_acc,
            "confusion_matrix": [[cv_tp, cv_fn], [cv_fp, cv_tn]],
            "true_positives": cv_tp,
            "true_negatives": cv_tn,
            "false_positives": cv_fp,
            "false_negatives": cv_fn,
            "far": round(cv_fp / (cv_fp + cv_tn), 4) if (cv_fp + cv_tn) > 0 else 0.0,
            "frr": round(cv_fn / (cv_fn + cv_tp), 4) if (cv_fn + cv_tp) > 0 else 0.0,
            "curva_umbral": curva,
            "umbral_decision": self.umbral_decision,
            "n_records": n_records,
            "n_positive": n_positive,
            "n_negative": n_negative,
            "model_type": self.model_type,
            "evaluacion": evaluacion,
            "metricas_fiables": metricas_fiables,
            "cv_accuracy": cv_accuracy,
            "cv_std": cv_std,
            "cv_gap": brecha,
            "cv_n_folds": n_splits,
            "overfitting": overfitting,
            "overfitting_msg": overfitting_msg,
        }

        if not metricas_fiables:
            metrics["warning"] = (
                f"Solo {n_records} registros ({n_positive} pos, {n_negative} neg). "
                "Las metricas pueden ser poco representativas. Recomendado: 50+ de cada clase."
            )

        logger.info(
            f"LogReg trained ({evaluacion}): CV_acc={cv_accuracy:.4f} | "
            f"train_acc={train_acc:.4f} | gap={brecha:.4f}"
        )
        return metrics

    def _train_logistic_regression(self, X: np.ndarray, y: np.ndarray, use_pca=False, pca=None) -> None:
        C = getattr(self, "_C", 0.01)
        n_features = X.shape[1] if X.ndim > 1 else 1
        self.model_type = f"LogReg+PCA({n_features}d)" if use_pca else "LogReg"
        self.base_model = LogisticRegression(
            C=C, penalty="l2", solver="lbfgs",
            class_weight="balanced", max_iter=2000, random_state=42,
        )

        unique_classes = len(np.unique(y))
        n_positive = int(y.sum())
        n_negative = len(X) - n_positive
        min_class = min(n_positive, n_negative)

        if unique_classes >= 2 and min_class >= 2:
            cv_folds = min(5, min_class)
            self.base_model.fit(X, y)
            n_records = len(X)
            cal_method = "isotonic" if n_records >= 8 else "sigmoid"
            self.calibrated_model = CalibratedClassifierCV(
                self.base_model, method=cal_method, cv=cv_folds
            )
            self.calibrated_model.fit(X, y)
            self.pca = pca
            logger.info(f"LogReg trained: C={C}, class_weight=balanced, cv={cv_folds}, cal={cal_method}")
        else:
            self.base_model.fit(X, y)
            self.calibrated_model = self.base_model
            self.pca = pca
            logger.info(f"LogReg trained (prefit, {len(X)} records, no calibration)")

    @staticmethod
    def _curva_far_frr(y_prob: np.ndarray, y_true: np.ndarray) -> list:
        """FAR y FRR para varios umbrales de decision (0.10 a 0.95).

        Permite ver el compromiso: subir el umbral baja el FAR (menos falsos
        aceptados) pero sube el FRR (mas humanos reales rechazados).
        """
        curva = []
        n = len(y_true)
        for thr_i in range(5, 96, 5):
            thr = thr_i / 100.0
            yp = (y_prob >= thr).astype(int)
            fp = int(((yp == 1) & (y_true == 0)).sum())
            tn = int(((yp == 0) & (y_true == 0)).sum())
            fn = int(((yp == 0) & (y_true == 1)).sum())
            tp = int(((yp == 1) & (y_true == 1)).sum())
            far = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
            frr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0
            acc = round((tp + tn) / n, 4) if n > 0 else 0.0
            curva.append({"umbral": thr, "far": far, "frr": frr, "accuracy": acc})
        return curva

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
        """Guarda el modelo calibrado, PCA y metricas como .joblib."""
        path = path or settings.ML_MODEL_PATH
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump({
            "model": self.calibrated_model,
            "model_type": self.model_type,
            "umbral_decision": getattr(self, "umbral_decision", settings.UMBRAL_DECISION),
            "pca": getattr(self, "pca", None),
        }, path)
        logger.info(f"Calibrated model saved to {path} (umbral={getattr(self, 'umbral_decision', settings.UMBRAL_DECISION)})")

    def load(self, path: str = None) -> None:
        """Carga un modelo calibrado y PCA desde .joblib."""
        path = path or settings.ML_MODEL_PATH
        data = joblib.load(path)
        if isinstance(data, dict):
            self.calibrated_model = data.get("model", data)
            self.model_type = data.get("model_type", type(self.calibrated_model).__name__)
            self.pca = data.get("pca", None)
        else:
            self.calibrated_model = data
            self.model_type = type(data).__name__
            self.pca = None
        logger.info(f"Calibrated model loaded from {path}")


def train_model():
    """Entrena el modelo unificado SOLO con datos reales del sistema.

    Features: similitud, distancia, calidad_imagen, iluminacion, textura,
    frecuencia_baja, frecuencia_alta, ruido, contraste_textura, asimetria,
    brillo_variacion, edge_consistency, fft_varianza, freq_edge_mean,
    freq_edge_var, lbp_mean, lbp_var, lbp_contraste, entropy, skin_smoothness (21 features).

    Kaggle NO se usa porque sus features son dummy 0.5 y arruinan el modelo.
    """
    try:
        from app.core.supabase_client import supabase_admin
        if not supabase_admin:
            logger.warning("train_model: Supabase not connected")
            return None

        result = supabase_admin.table("ml_training_records").select("*").execute()
        records = result.data or []

        if len(records) < 2:
            logger.warning(f"train_model: Not enough records ({len(records)}), need 2+")
            return None

        def _get_feat(r, key, default=0.5):
            v = r.get(key)
            if v is None:
                return default
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        X = np.array([[
            r.get("similitud") if r.get("similitud") is not None else 0.0,
            r.get("distancia") if r.get("distancia") is not None else 1.0,
            _get_feat(r, "calidad_imagen"),
            _get_feat(r, "iluminacion"),
            _get_feat(r, "textura", 0.5),
            _get_feat(r, "frecuencia_baja", 0.5),
            _get_feat(r, "frecuencia_alta", 0.5),
            _get_feat(r, "ruido", 0.5),
            _get_feat(r, "contraste_textura", 0.5),
            _get_feat(r, "asimetria", 0.5),
            _get_feat(r, "brillo_variacion", 0.5),
            _get_feat(r, "edge_consistency", 0.5),
            _get_feat(r, "fft_varianza", 0.5),
            _get_feat(r, "freq_edge_mean", 0.5),
            _get_feat(r, "freq_edge_var", 0.5),
            _get_feat(r, "lbp_mean", 0.5),
            _get_feat(r, "lbp_var", 0.5),
            _get_feat(r, "lbp_contraste", 0.5),
            _get_feat(r, "entropy", 0.5),
            _get_feat(r, "skin_smoothness", 0.5),
        ] for r in records])
        y = np.array([1 if r["resultado_real"] in (True, "true", "True", 1) else 0 for r in records])

        unique_classes = len(np.unique(y))
        if unique_classes < 2:
            logger.warning("train_model: Only one class in data, skipping")
            return None

        trainer = FaceTrainer()
        # 21 features: C=0.5 (regularizacion moderada). C=0.01 era para 512 dims y
        # subajustaba (Train ~72%). Con ~250 muestras y 21 features, 0.5 ajusta mejor
        # sin sobreajustar.
        trainer._C = 0.5
        metrics = trainer.train(X, y)
        trainer.save()
        logger.info(f"train_model: Success - accuracy={metrics.get('accuracy', 0):.4f}, records={len(records)}")
        return metrics
    except Exception as e:
        logger.error(f"train_model failed: {e}")
        return None


def _parse_embedding(raw):
    """Convierte el embedding de Supabase (string '[...]' o lista) a np.array."""
    import json
    if isinstance(raw, str):
        raw = json.loads(raw)
    return np.asarray(raw, dtype=np.float32)


def train_embedding_model():
    """Entrena el clasificador Real vs IA sobre el EMBEDDING de 512 dims.

    Lee ml_face_samples (embedding, es_real), entrena una Regresion Logistica
    regularizada (C=0.01) + calibracion + PCA, y guarda en EMB_MODEL_PATH.
    """
    try:
        import httpx
        from app.core.config import get_settings as _gs
        _s = _gs()

        # PostgREST directo (el SDK no lee ml_face_samples correctamente)
        headers = {
            "apikey": _s.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}",
        }
        resp = httpx.get(
            f"{_s.SUPABASE_URL}/rest/v1/ml_face_samples",
            params={"select": "embedding,es_real"},
            headers=headers, timeout=60,
        )
        if resp.status_code != 200:
            logger.error(f"train_embedding_model: PostgREST fetch failed {resp.status_code}")
            return None
        rows = resp.json() or []
        if not rows:
            logger.info("train_embedding_model: no ml_face_samples found")
            return None

        min_req = _s.MIN_TRAIN_PER_CLASS
        pos = sum(1 for r in rows if r.get("es_real") in (True, "true", "True", 1))
        neg = len(rows) - pos
        if pos < min_req or neg < min_req:
            logger.info(f"train_embedding_model: datos insuficientes ({pos} real, {neg} ia; need {min_req}+ c/u)")
            return None

        X = np.vstack([_parse_embedding(r["embedding"]) for r in rows])
        y = np.array([1 if r.get("es_real") in (True, "true", "True", 1) else 0 for r in rows])

        trainer = FaceTrainer()
        trainer._C = 0.01  # regularizacion fuerte para evitar overfitting
        metrics = trainer.train(X, y)
        metrics["feature_type"] = "embedding_512"
        trainer.save(settings.EMB_MODEL_PATH)
        logger.info(f"train_embedding_model: OK - accuracy={metrics.get('accuracy', 0):.4f}, n={len(rows)}")
        return metrics
    except Exception as e:
        logger.error(f"train_embedding_model failed: {e}")
        return None
