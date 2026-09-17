import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class FaceTrainer:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        logger.info(f"Model trained - Accuracy: {accuracy:.4f}")

        return {
            "accuracy": accuracy,
            "precision": report.get("1", {}).get("precision", 0),
            "recall": report.get("1", {}).get("recall", 0),
            "f1_score": report.get("1", {}).get("f1-score", 0),
        }

    def save(self, path: str = None):
        path = path or settings.ML_MODEL_PATH
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")

    def load(self, path: str = None):
        path = path or settings.ML_MODEL_PATH
        self.model = joblib.load(path)
        logger.info(f"Model loaded from {path}")
