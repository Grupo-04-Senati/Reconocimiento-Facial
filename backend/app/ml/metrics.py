import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
)
from app.core.logging_config import logger


class MLMetrics:
    @staticmethod
    def compute_all(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None) -> dict:
        metrics = {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        }

        if y_prob is not None:
            try:
                metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
            except ValueError:
                metrics["roc_auc"] = 0.0

        logger.info(f"ML Metrics: accuracy={metrics['accuracy']}, f1={metrics['f1_score']}")
        return metrics
