import uuid
from datetime import datetime, timezone
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger


class AuditService:
    def log_recognition(
        self,
        persona_id: str | None,
        similitud: float,
        distancia: float,
        umbral: float,
        coincide: bool,
        probabilidad_calibrada: float = None,
    ) -> dict:
        result = supabase_admin.table("recognition_logs").insert(
            {
                "persona_id": persona_id,
                "similitud": similitud,
                "distancia": distancia,
                "umbral": umbral,
                "coincide": coincide,
                "probabilidad_calibrada": probabilidad_calibrada,
            }
        ).execute()
        logger.info(
            f"Recognition log: persona={persona_id}, "
            f"similitud={similitud:.4f}, coincide={coincide}"
        )
        return result.data[0] if result.data else {}

    def log_training_record(self, features: dict, resultado_real: bool) -> dict:
        result = supabase_admin.table("ml_training_records").insert(
            {
                "similitud": features["similitud"],
                "calidad_imagen": features["calidad_imagen"],
                "iluminacion": features["iluminacion"],
                "distancia": features["distancia"],
                "resultado_real": resultado_real,
            }
        ).execute()
        logger.info(f"Training record saved: resultado_real={resultado_real}")
        return result.data[0] if result.data else {}

    def get_recent_logs(self, limit: int = 100) -> list:
        result = (
            supabase_admin.table("recognition_logs")
            .select("*, personas(nombre)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []


audit_service = AuditService()
