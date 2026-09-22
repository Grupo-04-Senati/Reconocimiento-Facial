"""Configuración de la aplicación con Pydantic Settings.

Justificación (PDF Sección 4): Variables de entorno para configuración
del backend, base de datos, modelos ML y seguridad.

Vercel: Lee variables de entorno configuradas en el dashboard.
Desarrollo: Lee de .env en la raíz de backend/.
Rutas de modelos: /tmp en Vercel (read-only), ./models en desarrollo.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración centralizada. Todas las variables se leen de entorno."""

    # --- Supabase ---
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_STORAGE_BUCKET: str = "face-images"
    SUPABASE_MODELS_BUCKET: str = "face-models"

    # --- Base de datos ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:54322/postgres"

    # --- Seguridad / JWT ---
    JWT_SECRET: str = "super-secret-jwt-token-with-at-least-32-characters-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- ML / Reconocimiento ---
    # Umbral de similitud coseno para aceptar una coincidencia con buffalo_s (ArcFace).
    # Rango típico: mismo rostro 0.4-0.7, rostros distintos < 0.3. Ajustable por entorno.
    UMBRAL_SIMILITUD: float = 0.40
    # Minimo de ejemplos por clase (Humano Real / No Real) para entrenar el ML.
    # 10 por clase da metricas creibles (con holdout real). Ajustable por entorno.
    MIN_TRAIN_PER_CLASS: int = 10
    # Umbral de decision del ML (probabilidad para aceptar como Humano Real).
    # Subirlo reduce el FAR (menos falsos aceptados) a costa de mas FRR. En
    # biometria se prioriza FAR bajo. El entrenador ajusta este valor por datos.
    UMBRAL_DECISION: float = 0.5

    # --- Entorno ---
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = ""

    # --- Vercel (automático) ---
    VERCEL_URL: str = ""
    VERCEL_ENV: str = ""

    @property
    def IS_VERCEL(self) -> bool:
        """True si se ejecuta en Vercel (producción o preview)."""
        return self.VERCEL_ENV in ("production", "preview") or bool(self.VERCEL_URL)

    @property
    def MODELS_DIR(self) -> str:
        """Directorio para modelos ONNX.
        Vercel: /tmp/models/ (único directorio writeable)
        Desarrollo: ./models/ (relativo a backend/)
        """
        if self.IS_VERCEL:
            return "/tmp/models"
        return os.path.join(os.path.dirname(__file__), "..", "..", "models")

    @property
    def ML_MODEL_PATH(self) -> str:
        """Ruta al modelo .joblib de calibración de probabilidades.
        En Vercel se almacena temporalmente en /tmp.
        """
        return os.path.join(self.MODELS_DIR, "probability_model.joblib")

    @property
    def EMB_MODEL_PATH(self) -> str:
        """Ruta al clasificador Real vs IA entrenado sobre el embedding 512-dim
        (features aprendidas de los pixeles por el DL). Es el modelo preferido;
        si no existe, el sistema usa el de 4 variables (ML_MODEL_PATH).
        """
        return os.path.join(self.MODELS_DIR, "embedding_model.joblib")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Singleton cacheado de Settings (se crea una vez por cold start)."""
    return Settings()
