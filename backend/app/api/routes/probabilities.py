from fastapi import APIRouter, HTTPException
from app.core.logging_config import logger

router = APIRouter(prefix="/api/probabilidades", tags=["probabilidades"])


def _get_supabase():
    try:
        from app.core.supabase_client import supabase_admin
        return supabase_admin
    except Exception as e:
        print(f"[probabilities] supabase error: {e}")
        return None


@router.post("/prediccion")
async def predecir(data: dict):
    try:
        from app.services.probability_service import probability_service
        prob = probability_service.predecir(data)
        return {"success": True, "probabilidad_calibrada": prob}
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Error en la prediccion")


@router.get("/estadisticas")
async def estadisticas():
    sb = _get_supabase()
    if sb is None:
        return {
            "success": True,
            "estadisticas": {
                "total_reconocimientos": 0,
                "coincidencias_positivas": 0,
                "tasa_exito": 0.0,
            },
            "warning": "Supabase no disponible",
        }
    try:
        total = sb.table("recognition_logs").select("*", count="exact").execute()
        positivos = (
            sb.table("recognition_logs")
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
        return {
            "success": True,
            "estadisticas": {
                "total_reconocimientos": 0,
                "coincidencias_positivas": 0,
                "tasa_exito": 0.0,
            },
            "warning": f"Error consultando BD: {str(e)[:100]}",
        }
