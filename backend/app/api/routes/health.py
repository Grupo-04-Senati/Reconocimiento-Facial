from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "Sistema de Reconocimiento Facial",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }
