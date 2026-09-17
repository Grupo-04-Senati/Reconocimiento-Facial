import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from app.core.logging_config import logger


class ProbabilityCalibrator:
    def __init__(self, base_model):
        self.base_model = base_model
        self.calibrated_model = None

    def calibrate(self, X: np.ndarray, y: np.ndarray, method: str = "isotonic"):
        self.calibrated_model = CalibratedClassifierCV(
            self.base_model, method=method, cv=5
        )
        self.calibrated_model.fit(X, y)
        logger.info(f"Model calibrated with method={method}")
        return self.calibrated_model

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.calibrated_model is None:
            return self.base_model.predict_proba(X)
        return self.calibrated_model.predict_proba(X)
