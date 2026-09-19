"""Aplicación FastAPI - Sistema Inteligente de Reconocimiento Facial.

Justificación PDF:
- Sección 4: Backend Python 3.11 + FastAPI + Uvicorn
- Sección 5: Pipeline de reconocimiento facial
- Sección 10: API REST con endpoints documentados
- Sección 15: Seguridad (CORS, autenticación, auditoría)

En Vercel:
  - Entry point: api/index.py → Mangum → FastAPI
  - Modelos ONNX se descargan de Supabase Storage a /tmp/models/
  - CORS maneja OPTIONS (preflight) automáticamente via CORSMiddleware
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import health, personas, recognition, probabilities, models
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

app = FastAPI(
    title="Sistema Inteligente de Reconocimiento Facial",
    version="1.0.0",
    description="API de IA, ML y DL para reconocimiento facial - Grupo 04 Senati",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS: permitir frontend en Vercel y desarrollo local
# CORSMiddleware maneja OPTIONS (preflight) automáticamente
_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
]
if settings.VERCEL_URL:
    _cors_origins.append(f"https://{settings.VERCEL_URL}")
if settings.CORS_ORIGINS:
    _cors_origins.extend(
        [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (prefijo /api ya incluido en cada router)
app.include_router(health.router)
app.include_router(personas.router)
app.include_router(recognition.router)
app.include_router(probabilities.router)
app.include_router(models.router)


@app.get("/api")
async def api_root():
    """Endpoint raíz de la API con información del servicio."""
    return {
        "message": "Sistema de Reconocimiento Facial - Grupo 04 Senati",
        "docs": "/api/docs",
        "health": "/api/health",
        "version": "1.0.0",
    }


# Manejador explícito para OPTIONS (preflight CORS)
# Aunque CORSMiddleware lo maneja, este endpoint garantiza respuestas 200
@app.options("/{path:path}")
async def options_handler(path: str):
    """Maneja requests OPTIONS (preflight CORS) para todos los endpoints."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Max-Age": "86400",
        },
    )


@app.on_event("startup")
async def startup_event():
    """Evento de inicio: descarga modelos ONNX si estamos en Vercel.

    Justificación (PDF Sección 4): El motor de IA utiliza InsightFace
    buffalo_l (SCRFD para detección + ArcFace R100 para embeddings de 512D).
    Los pesos .onnx se almacenan en Supabase Storage y se descargan a /tmp
    en el primer cold start.
    """
    logger.info("Starting Facial Recognition System API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Model base path: {settings.MODELS_DIR}")

    if settings.IS_VERCEL:
        try:
            from app.ml.model_loader import ensure_models_downloaded
            ensure_models_downloaded()
        except Exception as e:
            logger.warning(f"Model download failed (will retry on demand): {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Facial Recognition System API...")
