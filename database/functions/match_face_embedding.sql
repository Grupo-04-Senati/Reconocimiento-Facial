-- Eliminar funcion existente primero
DROP FUNCTION IF EXISTS match_face_embedding(vector, double precision, integer);

CREATE OR REPLACE FUNCTION match_face_embedding(
  query_embedding VECTOR(512),
  match_threshold FLOAT DEFAULT 0.40,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  persona_id uuid,
  nombre TEXT,
  similitud FLOAT,
  distancia FLOAT
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
    fe.embedding <=> query_embedding AS distancia
  FROM face_embeddings fe
  JOIN personas p ON p.id = fe.persona_id
  WHERE p.activo = TRUE
    AND 1 - (fe.embedding <=> query_embedding) > match_threshold
  ORDER BY fe.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
