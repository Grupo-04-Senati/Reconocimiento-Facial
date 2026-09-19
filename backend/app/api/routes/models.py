from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger
from app.core.config import get_settings

router = APIRouter(prefix="/api/modelos", tags=["models"])
settings = get_settings()


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase no conectado. Verifica la conexion a internet y las credenciales.",
        )


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
                    "name": "RandomForestClassifier + IsotonicCalibration",
                    "loaded": probability_service.model is not None,
                    "type": "probability_calibration",
                },
            },
        }
    except Exception as e:
        logger.error(f"Model status error: {e}")
        raise HTTPException(status_code=500, detail="Error checking model status")


@router.post("/entrenar")
async def entrenar_modelo():
    _check_supabase()
    try:
        from app.ml.trainer import FaceTrainer
        from app.ml.metrics import MLMetrics
        import numpy as np

        result = supabase_admin.table("ml_training_records").select("*").execute()
        records = result.data or []

        if len(records) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Se necesitan al menos 10 registros para entrenar. Hay {len(records)}.",
            )

        X = np.array([
            [
                r["similitud"],
                r["distancia"],
                r["calidad_imagen"],
                r["iluminacion"],
            ]
            for r in records
        ])
        y = np.array([1 if r["resultado_real"] else 0 for r in records])

        trainer = FaceTrainer()
        metrics = trainer.train(X, y)
        trainer.save(settings.ML_MODEL_PATH)

        from app.services.probability_service import ProbabilityService
        ProbabilityService._instance = None
        new_service = ProbabilityService()
        logger.info("ProbabilityService reloaded with calibrated model")

        y_pred = trainer.calibrated_model.predict(X)
        y_prob = trainer.calibrated_model.predict_proba(X)[:, 1]
        detailed_metrics = MLMetrics.compute_all(y, y_pred, y_prob)

        logger.info(f"Model trained: accuracy={metrics.get('accuracy', 0):.4f}")

        return {
            "success": True,
            "message": "RandomForest + Isotonic Calibracion entrenado exitosamente",
            "records_used": len(records),
            "model_type": "RandomForestClassifier (n=100, depth=10)",
            "calibration": "IsotonicRegression (cv=5)",
            "features": ["similitud", "distancia", "calidad_imagen", "iluminacion"],
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

        _check_supabase()

        result = supabase_admin.table("ml_training_records").select("*").execute()
        records = result.data or []

        from app.services.probability_service import probability_service
        is_loaded = probability_service.model is not None

        return {
            "success": True,
            "trained": True,
            "model_loaded": is_loaded,
            "model_class": model_info,
            "records_available": len(records),
            "model_path": settings.ML_MODEL_PATH,
            "metrics": {
                "model_type": "RandomForestClassifier",
                "calibration": "IsotonicRegression",
                "features": ["similitud", "distancia", "calidad_imagen", "iluminacion"],
                "threshold": settings.UMBRAL_SIMILITUD,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo metricas")
