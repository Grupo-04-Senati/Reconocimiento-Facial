CREATE TABLE IF NOT EXISTS ml_training_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  similitud FLOAT NOT NULL,
  calidad_imagen FLOAT NOT NULL,
  iluminacion FLOAT NOT NULL,
  distancia FLOAT NOT NULL,
  resultado_real BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
