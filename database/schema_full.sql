-- =============================================
-- SISTEMA DE RECONOCIMIENTO FACIAL - BADICORP
-- Script completo de base de datos
-- Ejecutar en Supabase SQL Editor
-- =============================================

-- 0. Extensiones
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- 1. TABLA: personas
-- =============================================
DROP TABLE IF EXISTS persona_stats CASCADE;
DROP TABLE IF EXISTS recognition_logs CASCADE;
DROP TABLE IF EXISTS ml_training_records CASCADE;
DROP TABLE IF EXISTS face_embeddings CASCADE;
DROP TABLE IF EXISTS personas CASCADE;

CREATE TABLE personas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  activo BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_personas_email ON personas(email);
CREATE INDEX idx_personas_activo ON personas(activo);

-- =============================================
-- 2. TABLA: face_embeddings
-- =============================================
CREATE TABLE face_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
  embedding VECTOR(512) NOT NULL,
  modelo TEXT NOT NULL DEFAULT 'buffalo_s',
  image_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_face_embeddings_persona ON face_embeddings(persona_id);

-- Indice HNSW para busqueda vectorial 1:N
CREATE INDEX idx_face_embeddings_hnsw ON face_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- =============================================
-- 3. TABLA: recognition_logs
-- =============================================
CREATE TABLE recognition_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
  similitud FLOAT NOT NULL,
  distancia FLOAT NOT NULL,
  umbral FLOAT NOT NULL,
  coincide BOOLEAN NOT NULL,
  probabilidad_calibrada FLOAT,
  resultado_real BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recognition_logs_persona ON recognition_logs(persona_id);
CREATE INDEX idx_recognition_logs_created ON recognition_logs(created_at DESC);

-- =============================================
-- 4. TABLA: ml_training_records
-- =============================================
CREATE TABLE ml_training_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  similitud DOUBLE PRECISION NOT NULL,
  calidad_imagen DOUBLE PRECISION NOT NULL,
  iluminacion DOUBLE PRECISION NOT NULL,
  distancia DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  resultado_real BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- 5. TABLA: users (autenticacion)
-- =============================================
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'operador' CHECK (role IN ('admin', 'operador', 'analista')),
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- 6. FUNCION: match_face_embedding
-- =============================================
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

-- =============================================
-- 7. ROW LEVEL SECURITY
-- =============================================
ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE face_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE recognition_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- personas: service_role full access
DROP POLICY IF EXISTS "personas_service_role" ON personas;
CREATE POLICY "personas_service_role" ON personas FOR ALL TO service_role USING (TRUE);

-- face_embeddings: service_role full access, anon block
DROP POLICY IF EXISTS "embeddings_service_role" ON face_embeddings;
DROP POLICY IF EXISTS "embeddings_no_public_access" ON face_embeddings;
CREATE POLICY "embeddings_service_role" ON face_embeddings FOR ALL TO service_role USING (TRUE);
CREATE POLICY "embeddings_no_public_access" ON face_embeddings FOR ALL TO anon USING (FALSE);

-- recognition_logs: service_role full access, authenticated read
DROP POLICY IF EXISTS "recognition_logs_service_role" ON recognition_logs;
DROP POLICY IF EXISTS "recognition_logs_authenticated_read" ON recognition_logs;
CREATE POLICY "recognition_logs_service_role" ON recognition_logs FOR ALL TO service_role USING (TRUE);
CREATE POLICY "recognition_logs_authenticated_read" ON recognition_logs FOR SELECT TO authenticated USING (TRUE);

-- users: service_role full access
DROP POLICY IF EXISTS "users_service_role" ON users;
CREATE POLICY "users_service_role" ON users FOR ALL TO service_role USING (TRUE);

-- =============================================
-- 8. ADMIN DEFAULT
-- =============================================
INSERT INTO users (name, email, password_hash, role, active)
VALUES (
  'Administrador',
  'admin@badicorp.com',
  '9b7a55e79398c38621ced664839781cc:875c26456d01e202277c5f1816ece79a555db7e15601317ec1ab413894905c0b',
  'admin',
  TRUE
) ON CONFLICT (email) DO NOTHING;

-- =============================================
-- FIN
-- =============================================
