from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger

router = APIRouter(prefix="/api/reconocimiento", tags=["reconocimiento"])
settings = get_settings()


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase no conectado. Verifica la conexión a internet y las credenciales.",
        )


@router.post("")
async def reconocer(imagen: UploadFile = File(...)):
    _check_supabase()
    try:
        from app.services.face_service import face_service
        from app.services.probability_service import probability_service
        from app.services.audit_service import audit_service

        image_bytes = await imagen.read()
        face_data = face_service.get_embedding_with_quality(image_bytes)
        embedding = face_data["embedding"]

        embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
        result = supabase_admin.rpc(
            "match_face_embedding",
            {
                "query_embedding": embedding_str,
                "match_threshold": settings.UMBRAL_SIMILITUD,
                "match_count": 1,
            },
        ).execute()

        if not result.data:
            audit_service.log_recognition(
                persona_id=None,
                similitud=0.0,
                distancia=1.0,
                umbral=settings.UMBRAL_SIMILITUD,
                coincide=False,
            )
            return {"success": True, "coincide": False, "resultado": None}

        match = result.data[0]
        features = {
            "similitud": match["similitud"],
            "distancia": match["distancia"],
            "calidad_imagen": face_data["quality"],
            "iluminacion": face_data["illumination"],
        }
        prob = probability_service.predecir(features)

        audit_service.log_recognition(
            persona_id=match["persona_id"],
            similitud=match["similitud"],
            distancia=match["distancia"],
            umbral=settings.UMBRAL_SIMILITUD,
            coincide=True,
            probabilidad_calibrada=prob,
        )

        return {
            "success": True,
            "resultado": {
                "persona_id": match["persona_id"],
                "nombre": match["nombre"],
                "similitud": round(match["similitud"], 4),
                "distancia": round(match["distancia"], 4),
                "umbral": settings.UMBRAL_SIMILITUD,
                "coincide": True,
                "probabilidad_calibrada": prob,
                "calidad_imagen": round(face_data["quality"], 4),
                "iluminacion": round(face_data["illumination"], 4),
            },
        }

    except ValueError as e:
        return {"success": True, "coincide": False, "resultado": None, "detail": str(e)}
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        raise HTTPException(status_code=500, detail="Error en el reconocimiento")


@router.get("/historial")
async def historial():
    _check_supabase()
    try:
        from app.services.audit_service import audit_service

        logs = audit_service.get_recent_logs(limit=100)
        return {"success": True, "historial": logs}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
