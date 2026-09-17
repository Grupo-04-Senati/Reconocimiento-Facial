from fastapi import APIRouter, HTTPException
from app.schemas.probability_schema import PrediccionInput, PrediccionResponse, TrainingRecordInput
from app.services.probability_service import probability_service
from app.services.audit_service import audit_service
from app.core.logging_config import logger

router = APIRouter(prefix="/api/probabilidades", tags=["probabilidades"])


@router.post("/prediccion", response_model=PrediccionResponse)
async def predecir(data: PrediccionInput):
    try:
        prob = probability_service.predecir(data.model_dump())
        return PrediccionResponse(success=True, probabilidad_calibrada=prob)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Error en la predicción")


@router.post("/entrenar")
async def registrar_registro(data: TrainingRecordInput):
    try:
        record = audit_service.log_training_record(
            features=data.model_dump(), resultado_real=data.resultado_real
        )
        return {"success": True, "record_id": record.get("id")}
    except Exception as e:
        logger.error(f"Training record error: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar")


@router.get("/estadisticas")
async def estadisticas():
    try:
        from app.core.supabase_client import supabase_admin

        total = supabase_admin.table("recognition_logs").select("*", count="exact").execute()
        positivos = (
            supabase_admin.table("recognition_logs")
            .select("*", count="exact")
            .eq("coincide", True)
            .execute()
        )
        total_count = total.count or 0
        positive_count = positivos.count or 0

        return {
            "success": True,
            "estadisticas": {
                "total_reconocimientos": total_count,
                "coincidencias_positivas": positive_count,
                "tasa_exito": round(positive_count / total_count, 4) if total_count > 0 else 0.0,
            },
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
