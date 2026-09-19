from __future__ import annotations
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
        self._load_model()
        self._initialized = True

    def _load_model(self):
        try:
            self.model = joblib.load(settings.ML_MODEL_PATH)
            model_type = type(self.model).__name__
            logger.info(f"ML model loaded: {model_type} from {settings.ML_MODEL_PATH}")
        except FileNotFoundError:
            logger.warning(
                f"ML model not found at {settings.ML_MODEL_PATH}. "
                "Using similarity-based fallback."
            )
        except Exception as e:
            logger.warning(f"Error loading ML model: {e}. Using fallback.")

    def reload(self):
        self.model = None
        self._initialized = False
        self.__init__()

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
