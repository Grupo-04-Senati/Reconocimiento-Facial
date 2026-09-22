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
        self.pca = None
        self.umbral_decision = settings.UMBRAL_DECISION
        self.emb_model = None
        self.emb_pca = None
        self.umbral_embedding = settings.UMBRAL_DECISION
        self._load_model()
        self._load_emb_model()
        self._initialized = True

    def _load_emb_model(self):
        """Carga el clasificador por embedding si existe (best-effort)."""
        try:
            data = joblib.load(settings.EMB_MODEL_PATH)
            if isinstance(data, dict):
                self.emb_model = data.get("model", data)
                self.emb_pca = data.get("pca", None)
                self.umbral_embedding = float(data.get("umbral_decision", settings.UMBRAL_DECISION))
            else:
                self.emb_model = data
                self.emb_pca = None
            logger.info(f"Embedding model loaded (umbral={self.umbral_embedding}) from {settings.EMB_MODEL_PATH}")
        except FileNotFoundError:
            self.emb_model = None
            self.emb_pca = None
        except Exception as e:
            logger.warning(f"Error loading embedding model: {e}")
            self.emb_model = None
            self.emb_pca = None

    def predecir_embedding(self, embedding) -> float | None:
        """P(Humano Real) a partir del embedding 512-dim. None si no hay modelo."""
        if self.emb_model is None:
            return None
        try:
            X = np.asarray(embedding, dtype=float).reshape(1, -1)
            if X.shape[1] < 100:
                return None
            if self.emb_pca is not None:
                X = self.emb_pca.transform(X)
            prob = float(self.emb_model.predict_proba(X)[0][1])
            return round(max(0.0, min(1.0, prob)), 4)
        except Exception as e:
            logger.error(f"Embedding prediction error: {e}")
            return None

    def _load_model(self):
        try:
            data = joblib.load(settings.ML_MODEL_PATH)
            if isinstance(data, dict):
                self.model = data.get("model", data)
                self.umbral_decision = float(data.get("umbral_decision", settings.UMBRAL_DECISION))
                self.pca = data.get("pca", None)
            else:
                self.model = data
                self.pca = None
            model_type = type(self.model).__name__
            pca_info = f" + PCA({self.pca.n_components_}d)" if self.pca is not None else ""
            logger.info(f"ML model loaded: {model_type}{pca_info} (umbral={self.umbral_decision}) from {settings.ML_MODEL_PATH}")
        except FileNotFoundError:
            logger.warning(f"ML model not found. Attempting auto-retrain from DB...")
            self._auto_retrain_from_db()
        except Exception as e:
            logger.warning(f"Error loading ML model: {e}. Attempting auto-retrain...")
            self._auto_retrain_from_db()

    def _auto_retrain_from_db(self):
        try:
            from app.core.config import get_settings as _gs
            _s = _gs()
            import httpx as _hx

            # PostgREST directo (SDK count roto)
            h = {"apikey": _s.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}"}
            r = _hx.get(f"{_s.SUPABASE_URL}/rest/v1/ml_training_records",
                       params={"select": "resultado_real"}, headers=h, timeout=30)
            if r.status_code != 200:
                logger.warning("Auto-retrain: PostgREST fetch failed")
                return
            rows = r.json() or []
            pos_count = sum(1 for row in rows if row.get("resultado_real") in (True, "true", "True", 1))
            neg_count = sum(1 for row in rows if row.get("resultado_real") in (False, "false", "False", 0))

            min_req = _s.MIN_TRAIN_PER_CLASS
            if pos_count >= min_req and neg_count >= min_req:
                from app.ml.trainer import train_model
                train_model()
                self.reload()
                logger.info(f"Auto-retrained ML model: {pos_count} pos, {neg_count} neg")
            else:
                logger.warning(f"Not enough data to train: {pos_count} pos, {neg_count} neg (need {min_req}+ each)")
        except Exception as e:
            logger.error(f"Auto-retrain failed: {e}")

    def reload(self):
        self.model = None
        self._initialized = False
        self.__init__()

    def predecir(self, features: dict) -> float:
        if self.model is None:
            return self._fallback_prediction(features)

        def _get_feat(key, default=0.5):
            v = features.get(key)
            if v is None:
                return default
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        X = np.array([[
            features.get("similitud", 0.0),
            features.get("distancia", 1.0),
            _get_feat("calidad_imagen"),
            _get_feat("iluminacion"),
            _get_feat("textura", 0.5),
            _get_feat("frecuencia_baja", 0.5),
            _get_feat("frecuencia_alta", 0.5),
            _get_feat("ruido", 0.5),
            _get_feat("contraste_textura", 0.5),
            _get_feat("asimetria", 0.5),
            _get_feat("brillo_variacion", 0.5),
            _get_feat("edge_consistency", 0.5),
            _get_feat("fft_varianza", 0.5),
            _get_feat("freq_edge_mean", 0.5),
            _get_feat("freq_edge_var", 0.5),
            _get_feat("lbp_mean", 0.5),
            _get_feat("lbp_var", 0.5),
            _get_feat("lbp_contraste", 0.5),
            _get_feat("entropy", 0.5),
            _get_feat("skin_smoothness", 0.5),
        ]])
        try:
            if self.pca is not None:
                X = self.pca.transform(X)
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
