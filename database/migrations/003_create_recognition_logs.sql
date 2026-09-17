CREATE TABLE IF NOT EXISTS recognition_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
  similitud FLOAT NOT NULL,
  distancia FLOAT NOT NULL,
  umbral FLOAT NOT NULL,
  coincide BOOLEAN NOT NULL,
  probabilidad_calibrada FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recognition_logs_persona ON recognition_logs(persona_id);
CREATE INDEX idx_recognition_logs_created ON recognition_logs(created_at DESC);
