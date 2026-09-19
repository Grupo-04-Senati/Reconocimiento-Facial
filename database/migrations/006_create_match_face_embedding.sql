-- =====================================================
-- Funcion match_face_embedding para busqueda vectorial 1:N
-- NOTA: La tabla face_embeddings ya existe con columna "embedding" (vector 512)
-- =====================================================

-- Asegurar que la extension pgvector esta habilitada
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear indice HNSW si no existe (usa la columna "embedding")
CREATE INDEX IF NOT EXISTS idx_face_embeddings_hnsw
ON face_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Eliminar funcion existente (necesario si los parametros cambiaron)
DROP FUNCTION IF EXISTS match_face_embedding(vector, double precision, integer);

-- Crear la funcion con la columna correcta "embedding" y JOIN con personas
CREATE OR REPLACE FUNCTION match_face_embedding(
    query_embedding vector(512),
    match_threshold float DEFAULT 0.40,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id int,
    persona_id UUID,
    nombre TEXT,
    similitud float,
    distancia float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fe.id,
        fe.persona_id,
        p.nombre,
        1 - (fe.embedding <=> query_embedding) AS similitud,
        (fe.embedding <=> query_embedding) AS distancia
    FROM face_embeddings fe
    JOIN personas p ON p.id = fe.persona_id
    WHERE p.activo = TRUE
      AND 1 - (fe.embedding <=> query_embedding) > match_threshold
    ORDER BY fe.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Verificar que la funcion existe
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_name = 'match_face_embedding';
