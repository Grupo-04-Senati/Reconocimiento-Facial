from fastapi import APIRouter, HTTPException
from app.core.logging_config import logger

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/status")
async def model_status():
    try:
        from app.services.face_service import face_service
        from app.services.probability_service import probability_service

        return {
            "success": True,
            "models": {
                "face_detection": {
                    "name": "buffalo_l (InsightFace)",
                    "loaded": face_service._initialized,
                    "type": "face_detection_embedding",
                },
                "probability": {
                    "name": "probability_model",
                    "loaded": probability_service.model is not None,
                    "type": "probability_calibration",
                },
            },
        }
    except Exception as e:
        logger.error(f"Model status error: {e}")
        raise HTTPException(status_code=500, detail="Error checking model status")
