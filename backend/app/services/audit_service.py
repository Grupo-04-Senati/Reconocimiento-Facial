from __future__ import annotations
from typing import Optional
import uuid
from datetime import datetime, timezone
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger


class AuditService:
    def log_recognition(
        self,
        persona_id: Optional[str],
        similitud: float,
        distancia: float,
        umbral: float,
        coincide: bool,
        probabilidad_calibrada: Optional[float] = None,
        calidad_imagen: Optional[float] = None,
        iluminacion: Optional[float] = None,
        resultado_real: Optional[bool] = None,
    ) -> dict:
        payload = {
            "persona_id": persona_id,
            "similitud": similitud,
            "distancia": distancia,
            "umbral": umbral,
            "coincide": coincide,
            "probabilidad_calibrada": probabilidad_calibrada,
        }
        # Se guardan calidad/iluminacion reales para que el ML entrene con datos
        # verdaderos (no defaults 0.5). Requiere migracion 011.
        if calidad_imagen is not None:
            payload["calidad_imagen"] = calidad_imagen
        if iluminacion is not None:
            payload["iluminacion"] = iluminacion
        # resultado_real: si viene ya etiquetado (carga masiva), el log queda
        # CONFIRMADO de una vez (no pendiente).
        if resultado_real is not None:
            payload["resultado_real"] = resultado_real

        try:
            result = supabase_admin.table("recognition_logs").insert(payload).execute()
        except Exception as e:
            # Fallback: si las columnas calidad_imagen/iluminacion aun no existen
            # (migracion 011 no aplicada), reintenta sin ellas para no perder el log.
            # IMPORTANTE: se conserva resultado_real (esa columna si existe) para que
            # una carga ya etiquetada (Seguridad) NO quede como "pendiente de decidir".
            logger.warning(f"log_recognition con columnas extra fallo ({e}); reintentando sin calidad/iluminacion")
            payload.pop("calidad_imagen", None)
            payload.pop("iluminacion", None)
            try:
                result = supabase_admin.table("recognition_logs").insert(payload).execute()
            except Exception as e2:
                logger.warning(f"log_recognition reintento fallo ({e2}); ultimo intento sin resultado_real")
                payload.pop("resultado_real", None)
                result = supabase_admin.table("recognition_logs").insert(payload).execute()

        logger.info(
            f"Recognition log: persona={persona_id}, "
            f"similitud={similitud:.4f}, coincide={coincide}"
        )
        return result.data[0] if result.data else {}

    def log_training_record(self, features: dict, resultado_real: bool) -> dict:
        payload = {
            "similitud": features["similitud"],
            "calidad_imagen": features["calidad_imagen"],
            "iluminacion": features["iluminacion"],
            "distancia": features["distancia"],
            "resultado_real": resultado_real,
        }
        # Features OpenCV para deteccion AI vs Humano
        for key in ("textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura",
                     "asimetria", "brillo_variacion", "edge_consistency",
                     "fft_varianza", "freq_edge_mean", "freq_edge_var",
                     "lbp_mean", "lbp_var", "lbp_contraste", "entropy", "skin_smoothness"):
            if features.get(key) is not None:
                payload[key] = features[key]
        # Embedding 512-dim para modelo de embedding
        if features.get("embedding") is not None:
            import json
            emb = features["embedding"]
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            payload["embedding"] = json.dumps(emb) if not isinstance(emb, str) else emb
        # Fuente del registro
        if features.get("fuente"):
            payload["fuente"] = features["fuente"]

        try:
            result = supabase_admin.table("ml_training_records").insert(payload).execute()
        except Exception as e:
            # Fallback: si las columnas nuevas aun no existen, inserta sin ellas
            logger.warning(f"log_training_record con columnas extra fallo ({e}); reintentando sin ellas")
            for key in ("textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura",
                        "asimetria", "brillo_variacion", "edge_consistency",
                        "fft_varianza", "freq_edge_mean", "freq_edge_var",
                        "lbp_mean", "lbp_var", "lbp_contraste", "entropy", "skin_smoothness",
                        "embedding", "fuente"):
                payload.pop(key, None)
            result = supabase_admin.table("ml_training_records").insert(payload).execute()

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
