from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
settings = get_settings()


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")


@router.get("/stats")
async def dashboard_stats(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        # Total personas
        personas_result = supabase_admin.table("personas").select("id", count="exact").execute()
        total_personas = personas_result.count or 0

        # Total embeddings
        embeddings_result = supabase_admin.table("face_embeddings").select("id", count="exact").execute()
        total_embeddings = embeddings_result.count or 0

        # Total reconocimientos
        logs_result = supabase_admin.table("recognition_logs").select("id", count="exact").execute()
        total_reconocimientos = logs_result.count or 0

        # Coincidencias positivas
        coincidencias = (
            supabase_admin.table("recognition_logs")
            .select("id", count="exact")
            .eq("coincide", True)
            .execute()
        )
        total_coincidencias = coincidencias.count or 0

        # Confirmados correctos / incorrectos
        correctos = (
            supabase_admin.table("recognition_logs")
            .select("id", count="exact")
            .eq("resultado_real", True)
            .execute()
        )
        incorrectos = (
            supabase_admin.table("recognition_logs")
            .select("id", count="exact")
            .eq("resultado_real", False)
            .execute()
        )

        # ML training records - PostgREST directo (SDK count roto)
        import httpx as _hx
        ml_h = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}
        try:
            ml_resp = _hx.get(f"{settings.SUPABASE_URL}/rest/v1/ml_training_records",
                             params={"select": "resultado_real"}, headers=ml_h, timeout=30)
            if ml_resp.status_code == 200:
                ml_rows = ml_resp.json() or []
                ml_total_count = len(ml_rows)
                ml_pos_count = sum(1 for r in ml_rows if r.get("resultado_real") in (True, "true", "True", 1))
                ml_neg_count = sum(1 for r in ml_rows if r.get("resultado_real") in (False, "false", "False", 0))
            else:
                ml_total_count = 0
                ml_pos_count = 0
                ml_neg_count = 0
        except Exception:
            ml_total_count = 0
            ml_pos_count = 0
            ml_neg_count = 0

        # Model status
        model_status = "no_entrenado"
        model_class = None
        try:
            import os
            import joblib
            if os.path.exists(settings.ML_MODEL_PATH):
                model = joblib.load(settings.ML_MODEL_PATH)
                model_class = type(model).__name__
                model_status = "activo"
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            model_status = "error"

        # Face service status
        face_status = "no_disponible"
        try:
            from app.services.face_service import face_service
            face_status = "activo" if face_service._initialized else "cargando"
        except Exception:
            face_status = "error"

        # Probability service status
        prob_status = "no_disponible"
        try:
            from app.services.probability_service import probability_service
            prob_status = "activo" if probability_service.model is not None else "fallback"
        except Exception:
            prob_status = "error"

        # Recognitions per day (last 7 days)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        daily_data = []
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            day_start = f"{day}T00:00:00"
            day_end = f"{day}T23:59:59"
            try:
                day_count = (
                    supabase_admin.table("recognition_logs")
                    .select("id", count="exact")
                    .gte("created_at", day_start)
                    .lte("created_at", day_end)
                    .execute()
                )
                pos_count = (
                    supabase_admin.table("recognition_logs")
                    .select("id", count="exact")
                    .gte("created_at", day_start)
                    .lte("created_at", day_end)
                    .eq("coincide", True)
                    .execute()
                )
                daily_data.append({
                    "fecha": day,
                    "total": day_count.count or 0,
                    "positivos": pos_count.count or 0,
                    "negativos": (day_count.count or 0) - (pos_count.count or 0),
                })
            except Exception:
                daily_data.append({"fecha": day, "total": 0, "positivos": 0, "negativos": 0})

        tasa_exito = total_coincidencias / total_reconocimientos if total_reconocimientos > 0 else 0

        return {
            "success": True,
            "resumen": {
                "total_personas": total_personas,
                "total_embeddings": total_embeddings,
                "total_reconocimientos": total_reconocimientos,
                "total_coincidencias": total_coincidencias,
                "tasa_exito": round(tasa_exito, 4),
                "confirmados_correctos": correctos.count or 0,
                "confirmados_incorrectos": incorrectos.count or 0,
            },
            "modelo_ml": {
                "estado": model_status,
                "clase": model_class,
                "registros_totales": ml_total_count,
                "registros_positivos": ml_pos_count,
                "registros_negativos": ml_neg_count,
            },
            "servicios": {
                "face_detection": face_status,
                "probability_model": prob_status,
                "supabase": "conectado",
            },
            "reconocimientos_por_dia": daily_data,
        }

    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadisticas: {str(e)[:200]}")
