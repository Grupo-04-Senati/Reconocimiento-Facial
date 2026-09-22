-- Fix: agregar columna distancia a ml_training_records
ALTER TABLE ml_training_records
  ADD COLUMN IF NOT EXISTS distancia DOUBLE PRECISION NOT NULL DEFAULT 0.0;
