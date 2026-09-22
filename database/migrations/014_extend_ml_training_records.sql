-- Migracion 014: Agregar features OpenCV a ml_training_records
-- Permite al modelo ML aprender de textura, FFT, ruido, LBP, etc.

ALTER TABLE ml_training_records
  ADD COLUMN IF NOT EXISTS textura FLOAT,
  ADD COLUMN IF NOT EXISTS frecuencia_baja FLOAT,
  ADD COLUMN IF NOT EXISTS frecuencia_alta FLOAT,
  ADD COLUMN IF NOT EXISTS ruido FLOAT,
  ADD COLUMN IF NOT EXISTS contraste_textura FLOAT,
  ADD COLUMN IF NOT EXISTS asimetria FLOAT,
  ADD COLUMN IF NOT EXISTS brillo_variacion FLOAT,
  ADD COLUMN IF NOT EXISTS edge_consistency FLOAT,
  ADD COLUMN IF NOT EXISTS fft_varianza FLOAT,
  ADD COLUMN IF NOT EXISTS freq_edge_mean FLOAT,
  ADD COLUMN IF NOT EXISTS freq_edge_var FLOAT,
  ADD COLUMN IF NOT EXISTS lbp_mean FLOAT,
  ADD COLUMN IF NOT EXISTS lbp_var FLOAT,
  ADD COLUMN IF NOT EXISTS lbp_contraste FLOAT,
  ADD COLUMN IF NOT EXISTS entropy FLOAT,
  ADD COLUMN IF NOT EXISTS skin_smoothness FLOAT,
  ADD COLUMN IF NOT EXISTS embedding JSONB,
  ADD COLUMN IF NOT EXISTS fuente VARCHAR(50) DEFAULT 'sistema';

CREATE INDEX IF NOT EXISTS idx_ml_training_records_fuente ON ml_training_records(fuente);
