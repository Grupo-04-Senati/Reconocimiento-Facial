"""Servicio de embeddings faciales.

Genera embeddings con InsightFace/ArcFace y los almacena en Supabase.
"""
import numpy as np
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger


class EmbeddingService:
    def generate_embedding(self, image_bytes: bytes) -> np.ndarray:
        from app.services.face_service import face_service
        if not face_service._initialized:
            raise RuntimeError("Modelo facial no inicializado")
        return face_service.get_embedding(image_bytes)

    def generate_embedding_with_quality(self, image_bytes: bytes) -> dict:
        from app.services.face_service import face_service
        if not face_service._initialized:
            raise RuntimeError("Modelo facial no inicializado")
        return face_service.get_embedding_with_quality(image_bytes)

    def save_embedding(
        self,
        persona_id: str,
        embedding: np.ndarray,
        modelo: str = "buffalo_s",
    ) -> dict:
        if supabase_admin is None:
            raise RuntimeError("Supabase no conectado")
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        result = supabase_admin.table("face_embeddings").insert(
            {
                "persona_id": str(persona_id),
                "embedding": embedding_list,
                "modelo": modelo,
            }
        ).execute()
        logger.info(f"Embedding saved for persona {persona_id}")
        return result.data[0] if result.data else {}

    def get_embeddings_by_persona(self, persona_id: str) -> list:
        if supabase_admin is None:
            return []
        result = (
            supabase_admin.table("face_embeddings")
            .select("*")
            .eq("persona_id", persona_id)
            .execute()
        )
        return result.data or []

    def delete_embeddings_by_persona(self, persona_id: str) -> bool:
        if supabase_admin is None:
            return False
        supabase_admin.table("face_embeddings").delete().eq(
            "persona_id", persona_id
        ).execute()
        logger.info(f"Embeddings deleted for persona {persona_id}")
        return True


embedding_service = EmbeddingService()
