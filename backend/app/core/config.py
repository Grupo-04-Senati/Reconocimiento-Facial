from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_STORAGE_BUCKET: str = "face-images"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:54322/postgres"
    JWT_SECRET: str = "super-secret-jwt-token-with-at-least-32-characters-long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    FACE_MODEL_PATH: str = "./models/arcface.onnx"
    ML_MODEL_PATH: str = "./models/probability_model.joblib"
    UMBRAL_SIMILITUD: float = 0.40
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
