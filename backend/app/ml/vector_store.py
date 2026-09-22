from __future__ import annotations
import numpy as np
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class VectorStore:
    """Cliente pgvector para búsqueda facial 1:N con índice HNSW.

    Justificación (PDF Sección 5):
      - Los embeddings faciales de 512 dimensiones se almacenan como VECTOR(512).
      - La búsqueda 1:N se realiza con distancia coseno (operador <=>).
      - Se utiliza índice HNSW (m=16, ef_construction=64) por su superioridad
        sobre ivfflat en consultas de alto rendimiento con baja latencia.

    Justificación (PDF Sección 11):
      - Tabla face_embeddings: id, persona_id, embedding (vector 512), modelo,
        image_url, created_at.
      - La función RPC match_face_embedding retorna persona_id, nombre,
        similitud y distancia.
    """

    def search_similar(
        self,
        query_embedding: np.ndarray,
        threshold: float = None,
        match_count: int = 5,
    ) -> list[dict]:
        if threshold is None:
            threshold = settings.UMBRAL_SIMILITUD

        embedding_str = _embedding_to_string(query_embedding)

        try:
            result = supabase_admin.rpc(
                "match_face_embedding",
                {
                    "query_embedding": embedding_str,
                    "match_threshold": threshold,
                    "match_count": match_count,
                },
            ).execute()

            matches = result.data or []
            if matches:
                logger.info(
                    f"Vector search (RPC): {len(matches)} matches above threshold {threshold}"
                )
                return matches
        except Exception as e:
            logger.warning(f"RPC match_face_embedding failed: {e}, using Python fallback")

        try:
            all_embeddings = supabase_admin.table("face_embeddings").select(
                "id, persona_id, embedding, modelo"
            ).execute()
            if not all_embeddings.data:
                return []

            scored = []
            for emb_row in all_embeddings.data:
                stored = emb_row.get("embedding")
                if stored is None:
                    continue
                if isinstance(stored, str):
                    try:
                        import json
                        stored = json.loads(stored)
                    except Exception:
                        continue
                stored_arr = np.array(stored, dtype=np.float32)
                norm_q = np.linalg.norm(query_embedding)
                norm_s = np.linalg.norm(stored_arr)
                if norm_q == 0 or norm_s == 0:
                    continue
                sim = float(np.dot(query_embedding, stored_arr) / (norm_q * norm_s))
                dist = 1.0 - sim
                if sim >= threshold:
                    persona_data = None
                    try:
                        p = supabase_admin.table("personas").select(
                            "id, nombre, email"
                        ).eq("id", emb_row["persona_id"]).execute()
                        if p.data:
                            persona_data = p.data[0]
                    except Exception:
                        pass
                    scored.append({
                        "persona_id": emb_row["persona_id"],
                        "nombre": persona_data.get("nombre") if persona_data else None,
                        "email": persona_data.get("email") if persona_data else None,
                        "similitud": round(sim, 4),
                        "distancia": round(dist, 4),
                        "id": emb_row["id"],
                    })

            scored.sort(key=lambda x: x["similitud"], reverse=True)
            matches = scored[:match_count]
            logger.info(
                f"Vector search (Python): {len(matches)} matches above threshold {threshold}"
            )
            return matches
        except Exception as e:
            logger.error(f"Python vector search failed: {e}")
            return []

    def save_embedding(
        self,
        persona_id: str,
        embedding: np.ndarray,
        modelo: str = "buffalo_s",
    ) -> dict:
        embedding_str = _embedding_to_string(embedding)

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

    def count_embeddings(self) -> int:
        result = supabase_admin.table("face_embeddings").select(
            "*", count="exact"
        ).execute()
        return result.count or 0


def _embedding_to_string(embedding: np.ndarray) -> str:
    return "[" + ",".join(str(float(x)) for x in embedding) + "]"


vector_store = VectorStore()
