import numpy as np
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger


class EmbeddingService:
    def save_embedding(
        self,
        persona_id: str,
        embedding: np.ndarray,
        modelo: str = "arcface",
        image_url: str = None,
    ) -> dict:
        result = supabase_admin.table("face_embeddings").insert(
            {
                "persona_id": persona_id,
                "embedding": embedding.tolist(),
                "modelo": modelo,
                "image_url": image_url,
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
