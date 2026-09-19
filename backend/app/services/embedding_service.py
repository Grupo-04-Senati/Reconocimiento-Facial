"""DEPRECATED: Usar app.ml.vector_store en su lugar.

Este módulo se mantiene por compatibilidad. El módulo vector_store.py
centraliza toda la lógica de pgvector con índice HNSW.
"""
import numpy as np
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger


class EmbeddingService:
    def save_embedding(
        self,
        persona_id: str,
        embedding: np.ndarray,
        modelo: str = "buffalo_s",
    ) -> dict:
        embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
        result = supabase_admin.table("face_embeddings").insert(
            {
                "persona_id": str(persona_id),
                "embedding": embedding_str,
                "modelo": modelo,
            }
        ).execute()
        logger.info(f"Embedding saved for persona {persona_id}")
        return result.data[0] if result.data else {}

    def get_embeddings_by_persona(self, persona_id: str) -> list:
        result = (
            supabase_admin.table("face_embeddings")
            .select("*")
            .eq("persona_id", persona_id)
            .execute()
        )
        return result.data or []

    def delete_embeddings_by_persona(self, persona_id: str) -> bool:
        supabase_admin.table("face_embeddings").delete().eq(
            "persona_id", persona_id
        ).execute()
        logger.info(f"Embeddings deleted for persona {persona_id}")
        return True


embedding_service = EmbeddingService()
