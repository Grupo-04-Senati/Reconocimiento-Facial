CREATE TABLE IF NOT EXISTS face_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
  embedding VECTOR(512) NOT NULL,
  modelo TEXT NOT NULL DEFAULT 'arcface',
  image_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_face_embeddings_persona ON face_embeddings(persona_id);

CREATE INDEX idx_face_embeddings_hnsw ON face_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
