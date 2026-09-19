from __future__ import annotations
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class FaceTrainer:
    def __init__(self):
        self.base_model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )
        self.calibrated_model = None

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.base_model.fit(X_train, y_train)

        self.calibrated_model = CalibratedClassifierCV(
            self.base_model, method="isotonic", cv=min(5, len(X_train) // 2)
        )
        self.calibrated_model.fit(X_train, y_train)

        y_pred = self.calibrated_model.predict(X_test)
        y_prob = self.calibrated_model.predict_proba(X_test)[:, 1]
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        tp = int(((y_pred == 1) & (y_test == 1)).sum())
        tn = int(((y_pred == 0) & (y_test == 0)).sum())
        fp = int(((y_pred == 1) & (y_test == 0)).sum())
        fn = int(((y_pred == 0) & (y_test == 1)).sum())

        logger.info(f"Model trained - Accuracy: {accuracy:.4f}")

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(report.get("1", {}).get("precision", 0), 4),
            "recall": round(report.get("1", {}).get("recall", 0), 4),
            "f1_score": round(report.get("1", {}).get("f1-score", 0), 4),
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
        }

    def save(self, path: str = None):
        path = path or settings.ML_MODEL_PATH
        joblib.dump(self.calibrated_model, path)
        logger.info(f"Calibrated model saved to {path}")

    def load(self, path: str = None):
        path = path or settings.ML_MODEL_PATH
        self.calibrated_model = joblib.load(path)
        logger.info(f"Calibrated model loaded from {path}")
