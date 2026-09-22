-- Fix: calidad_imagen e iluminacion deben ser FLOAT, no varchar
ALTER TABLE ml_training_records
  ALTER COLUMN calidad_imagen TYPE DOUBLE PRECISION USING calidad_imagen::DOUBLE PRECISION,
  ALTER COLUMN iluminacion TYPE DOUBLE PRECISION USING iluminacion::DOUBLE PRECISION;
