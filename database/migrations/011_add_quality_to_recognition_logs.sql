-- Migración 011: agregar calidad_imagen e iluminacion a recognition_logs
--
-- Motivo: el backend (confirmar/recalcular) y el pipeline ML usan estas
-- variables como features del modelo, pero la tabla recognition_logs no las
-- almacenaba. Sin estas columnas, al confirmar un reconocimiento se guardaban
-- valores falsos (0.5) en ml_training_records, degradando el entrenamiento.
--
-- Estas columnas son opcionales (NULL) para no romper registros existentes.

ALTER TABLE recognition_logs
  ADD COLUMN IF NOT EXISTS calidad_imagen FLOAT,
  ADD COLUMN IF NOT EXISTS iluminacion FLOAT;

COMMENT ON COLUMN recognition_logs.calidad_imagen IS 'Nitidez del rostro capturado [0,1] (Laplacian variance normalizada). Feature del modelo ML.';
COMMENT ON COLUMN recognition_logs.iluminacion IS 'Iluminacion promedio del rostro [0,1] (brillo normalizado). Feature del modelo ML.';
