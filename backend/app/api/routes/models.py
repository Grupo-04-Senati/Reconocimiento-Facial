from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.logging_config import logger
from app.core.config import get_settings

router = APIRouter(prefix="/api/modelos", tags=["models"])
settings = get_settings()


def _get_supabase():
    try:
        from app.core.supabase_client import supabase_admin
        if supabase_admin is not None:
            return supabase_admin
    except Exception as e:
        print(f"[models] supabase import error: {e}")
    return None


@router.get("/status")
async def model_status():
    try:
        supabase_status = "no disponible"
        try:
            sb = _get_supabase()
            if sb is not None:
                sb.table("personas").select("id").limit(1).execute()
                supabase_status = "conectado"
        except Exception as e:
            print(f"[status] Supabase error: {e}")
            supabase_status = f"error: {str(e)[:100]}"

        face_status = "no disponible"
        try:
            from app.services.face_service import face_service
            face_status = "cargado" if face_service._initialized else "lazy (no cargado)"
        except Exception as e:
            print(f"[status] Face service error: {e}")
            face_status = f"error: {str(e)[:100]}"

        prob_status = "no disponible"
        try:
            from app.services.probability_service import probability_service
            prob_status = "cargado" if probability_service.model is not None else "lazy (no cargado)"
        except Exception as e:
            print(f"[status] Probability service error: {e}")
            prob_status = f"error: {str(e)[:100]}"

        return {
            "success": True,
            "supabase": supabase_status,
            "models": {
                "face_detection": face_status,
                "probability": prob_status,
            },
        }
    except Exception as e:
        print(f"[status] Error general: {e}")
        return {
            "success": False,
            "supabase": "error",
            "error": str(e)[:200],
        }


@router.post("/entrenar")
async def entrenar_modelo():
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    try:
        from app.ml.trainer import FaceTrainer
        from app.ml.metrics import MLMetrics
        import numpy as np

        result = sb.table("ml_training_records").select("*").execute()
        records = result.data or []

        if len(records) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Se necesitan al menos 10 registros para entrenar. Hay {len(records)}.",
            )

        X = np.array([
            [r["similitud"], r["distancia"], r["calidad_imagen"], r["iluminacion"]]
            for r in records
        ])
        y = np.array([1 if r["resultado_real"] else 0 for r in records])

        trainer = FaceTrainer()
        metrics = trainer.train(X, y)
        trainer.save(settings.ML_MODEL_PATH)

        y_pred = trainer.calibrated_model.predict(X)
        y_prob = trainer.calibrated_model.predict_proba(X)[:, 1]
        detailed_metrics = MLMetrics.compute_all(y, y_pred, y_prob)

        return {
            "success": True,
            "message": "Modelo entrenado exitosamente",
            "records_used": len(records),
            "metrics": metrics,
            "detailed_metrics": detailed_metrics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail="Error durante el entrenamiento")


@router.get("/metricas")
async def obtener_metricas():
    try:
        import os
        import joblib

        if not os.path.exists(settings.ML_MODEL_PATH):
            return {
                "success": True,
                "trained": False,
                "message": "No hay modelo entrenado disponible",
                "metrics": None,
            }

        try:
            model = joblib.load(settings.ML_MODEL_PATH)
            model_info = type(model).__name__
        except Exception:
            model_info = "unknown"

        return {
            "success": True,
            "trained": True,
            "model_class": model_info,
            "model_path": settings.ML_MODEL_PATH,
            "metrics": {
                "model_type": "model",
                "features": ["similitud", "distancia", "calidad_imagen", "iluminacion"],
                "threshold": settings.UMBRAL_SIMILITUD,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo metricas")
