from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger
from app.ml.vector_store import vector_store

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
        from app.services.audit_service import audit_service
        from app.services.probability_service import probability_service

        print(f"[reconocimiento] Iniciando procesamiento de imagen")
        print(f"[reconocimiento] Modelo cargado: {face_service._initialized}")

        if not face_service._initialized:
            raise HTTPException(
                status_code=503,
                detail="Modelo IA no disponible. Intenta de nuevo en unos segundos.",
            )

        image_bytes = await imagen.read()
        print(f"[reconocimiento] Imagen bytes: {len(image_bytes)}")

        face_data = face_service.get_embedding_with_quality(image_bytes)
        embedding = face_data["embedding"]

        matches = vector_store.search_similar(
            query_embedding=embedding,
            threshold=settings.UMBRAL_SIMILITUD,
            match_count=5,
        )

        if not matches:
            audit_service.log_recognition(
                persona_id=None,
                similitud=0.0,
                distancia=1.0,
                umbral=settings.UMBRAL_SIMILITUD,
                coincide=False,
            )
            return {"success": True, "coincide": False, "resultado": None}

        best_match = matches[0]
        features = {
            "similitud": best_match["similitud"],
            "distancia": best_match["distancia"],
            "calidad_imagen": face_data["quality"],
            "iluminacion": face_data["illumination"],
        }
        prob = probability_service.predecir(features)

        audit_service.log_recognition(
            persona_id=best_match["persona_id"],
            similitud=best_match["similitud"],
            distancia=best_match["distancia"],
            umbral=settings.UMBRAL_SIMILITUD,
            coincide=True,
            probabilidad_calibrada=prob,
        )

        return {
            "success": True,
            "resultado": {
                "persona_id": best_match["persona_id"],
                "nombre": best_match["nombre"],
                "similitud": round(best_match["similitud"], 4),
                "distancia": round(best_match["distancia"], 4),
                "umbral": settings.UMBRAL_SIMILITUD,
                "coincide": True,
                "probabilidad_calibrada": prob,
                "calidad_imagen": round(face_data["quality"], 4),
                "iluminacion": round(face_data["illumination"], 4),
            },
            "top_matches": [
                {
                    "persona_id": m["persona_id"],
                    "nombre": m["nombre"],
                    "similitud": round(m["similitud"], 4),
                    "distancia": round(m["distancia"], 4),
                }
                for m in matches
            ],
        }

    except ValueError as e:
        return {"success": True, "coincide": False, "resultado": None, "detail": str(e)}
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        raise HTTPException(status_code=500, detail="Error en el reconocimiento")


@router.get("/historial")
async def historial():
    try:
        from app.services.audit_service import audit_service
        logs = audit_service.get_recent_logs(limit=100)
        return {"success": True, "historial": logs or []}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"success": True, "historial": [], "warning": f"Error: {str(e)[:100]}"}
