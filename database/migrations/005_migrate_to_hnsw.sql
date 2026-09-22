-- Migración: ivfflat → HNSW para búsqueda facial 1:N
-- Ejecutar en Supabase SQL Editor si la tabla face_embeddings ya existe
-- con índice ivfflat.

-- 1. Eliminar índice ivfflat anterior (si existe)
DROP INDEX IF EXISTS idx_face_embeddings_vector;

-- 2. Crear índice HNSW con parámetros del PDF (Sección 5)
--    m=16: conexiones por nodo
--    ef_construction=64: precisión en construcción del grafo
--    vector_cosine_ops: operador de similitud coseno
CREATE INDEX idx_face_embeddings_hnsw ON face_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 3. Actualizar umbral por defecto en la función RPC (de 0.75 a 0.40)
CREATE OR REPLACE FUNCTION match_face_embedding(
  query_embedding VECTOR(512),
  match_threshold FLOAT DEFAULT 0.40,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  persona_id UUID,
  nombre TEXT,
  similitud FLOAT,
  distancia FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id AS persona_id,
    p.nombre,
    1 - (fe.embedding <=> query_embedding) AS similitud,
    fe.embedding <=> query_embedding AS distancia
  FROM face_embeddings fe
  JOIN personas p ON p.id = fe.persona_id
  WHERE p.activo = TRUE
    AND 1 - (fe.embedding <=> query_embedding) > match_threshold
  ORDER BY fe.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
