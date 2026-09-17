import joblib
import numpy as np
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class ProbabilityService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.model = None
        try:
            self.model = joblib.load(settings.ML_MODEL_PATH)
            logger.info(f"ML model loaded from {settings.ML_MODEL_PATH}")
        except FileNotFoundError:
            logger.warning(
                f"ML model not found at {settings.ML_MODEL_PATH}. "
                "Using similarity-based fallback."
            )
        self._initialized = True

    def predecir(self, features: dict) -> float:
        if self.model is None:
            return self._fallback_prediction(features)

        X = np.array(
            [
                [
                    features["similitud"],
                    features["distancia"],
                    features["calidad_imagen"],
                    features["iluminacion"],
                ]
            ]
        )
        try:
            prob = float(self.model.predict_proba(X)[0][1])
            return round(max(0.0, min(1.0, prob)), 4)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._fallback_prediction(features)

    def _fallback_prediction(self, features: dict) -> float:
        sim = features.get("similitud", 0.0)
        quality = features.get("calidad_imagen", 0.5)
        illumination = features.get("iluminacion", 0.5)
        prob = sim * 0.7 + quality * 0.15 + illumination * 0.15
        return round(max(0.0, min(1.0, prob)), 4)


probability_service = ProbabilityService()
