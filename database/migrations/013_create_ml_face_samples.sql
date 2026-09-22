-- Migración 013: muestras faciales para el clasificador Real vs IA por EMBEDDING
--
-- Motivo: el ML pasa a aprender del embedding de 512 dimensiones que el DL extrae
-- de los pixeles (mucho mejor para distinguir Humano Real vs IA que 4 escalares).
-- Estas muestras son DATOS DE ENTRENAMIENTO internos: NO son personas enroladas
-- (no aparecen en 'registros' ni en la busqueda 1:N).
--
-- Se alimenta desde:
--   - la carga masiva de Seguridad (agregar-muestra), y
--   - el importador del dataset de Kaggle (scripts/importar_kaggle.py).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ml_face_samples (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  embedding VECTOR(512) NOT NULL,
  es_real BOOLEAN NOT NULL,
  fuente TEXT DEFAULT 'manual',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ml_face_samples_es_real ON ml_face_samples(es_real);

COMMENT ON TABLE ml_face_samples IS 'Embeddings 512-dim etiquetados (real/ia) para entrenar el clasificador Real vs IA. Datos internos, no son personas enroladas.';
COMMENT ON COLUMN ml_face_samples.es_real IS 'true = rostro de humano real; false = rostro generado por IA / no real.';
COMMENT ON COLUMN ml_face_samples.fuente IS 'Origen de la muestra: manual (carga Seguridad) o kaggle (dataset importado).';
