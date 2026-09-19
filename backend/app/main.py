from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, personas, recognition, probabilities, models
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

app = FastAPI(
    title="Sistema Inteligente de Reconocimiento Facial",
    version="1.0.0",
    description="API de IA, ML y DL para reconocimiento facial - Grupo 04 Senati",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://reconocimiento-facial-*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(personas.router)
app.include_router(recognition.router)
app.include_router(probabilities.router)
app.include_router(models.router)


@app.get("/")
async def root():
    return {
        "message": "Sistema de Reconocimiento Facial - Grupo 04 Senati",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Facial Recognition System API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Facial Recognition System API...")
