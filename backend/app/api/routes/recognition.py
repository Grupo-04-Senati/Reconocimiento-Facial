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

        print(f"[reconocimiento] === INICIO ===")
        print(f"[reconocimiento] Modelo cargado: {face_service._initialized}")

        if not face_service._initialized:
            raise HTTPException(
                status_code=503,
                detail="Modelo IA no disponible. Intenta de nuevo en unos segundos.",
            )

        image_bytes = await imagen.read()
        print(f"[reconocimiento] Imagen: {len(image_bytes)} bytes")

        print(f"[reconocimiento] Paso 1: Obteniendo embedding...")
        face_data = face_service.get_embedding_with_quality(image_bytes)
        embedding = face_data["embedding"]
        print(f"[reconocimiento] Embedding: shape={embedding.shape}")

        print(f"[reconocimiento] Paso 2: Buscando en pgvector...")
        matches = vector_store.search_similar(
            query_embedding=embedding,
            threshold=settings.UMBRAL_SIMILITUD,
            match_count=5,
        )
        print(f"[reconocimiento] Matches encontrados: {len(matches)}")

        if not matches:
            print(f"[reconocimiento] Sin matches, registrando en audit...")
            try:
                audit_service.log_recognition(
                    persona_id=None,
                    similitud=0.0,
                    distancia=1.0,
                    umbral=settings.UMBRAL_SIMILITUD,
                    coincide=False,
                )
                print(f"[reconocimiento] Audit registrado OK")
            except Exception as e:
                print(f"[reconocimiento] ERROR audit: {type(e).__name__}: {e}")
            return {"success": True, "coincide": False, "resultado": None}

        best_match = matches[0]
        print(f"[reconocimiento] Mejor match: persona_id={best_match.get('persona_id')}, similitud={best_match.get('similitud')}")

        features = {
            "similitud": best_match["similitud"],
            "distancia": best_match["distancia"],
            "calidad_imagen": face_data["quality"],
            "iluminacion": face_data["illumination"],
        }
        print(f"[reconocimiento] Paso 3: Predecir probabilidad...")
        try:
            prob = probability_service.predecir(features)
            print(f"[reconocimiento] Probabilidad: {prob}")
        except Exception as e:
            print(f"[reconocimiento] ERROR probabilidad: {type(e).__name__}: {e}")
            prob = None

        print(f"[reconocimiento] Paso 4: Registrando en audit...")
        try:
            audit_service.log_recognition(
                persona_id=best_match["persona_id"],
                similitud=best_match["similitud"],
                distancia=best_match["distancia"],
                umbral=settings.UMBRAL_SIMILITUD,
                coincide=True,
                probabilidad_calibrada=prob,
            )
            print(f"[reconocimiento] Audit registrado OK")
        except Exception as e:
            print(f"[reconocimiento] ERROR audit: {type(e).__name__}: {e}")

        print(f"[reconocimiento] === FIN OK ===")
        return {
            "success": True,
            "resultado": {
                "persona_id": best_match["persona_id"],
                "nombre": best_match.get("nombre", "N/A"),
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
                    "persona_id": m.get("persona_id"),
                    "nombre": m.get("nombre", "N/A"),
                    "similitud": round(m["similitud"], 4),
                    "distancia": round(m["distancia"], 4),
                }
                for m in matches
            ],
        }

    except HTTPException:
        raise
    except ValueError as e:
        print(f"[reconocimiento] ValueError: {e}")
        return {"success": True, "coincide": False, "resultado": None, "detail": str(e)}
    except Exception as e:
        print(f"[reconocimiento] ERROR GENERAL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el reconocimiento: {str(e)[:200]}")


@router.get("/historial")
async def historial():
    try:
        from app.services.audit_service import audit_service
        logs = audit_service.get_recent_logs(limit=100)
        return {"success": True, "historial": logs or []}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"success": True, "historial": [], "warning": f"Error: {str(e)[:100]}"}
