-- Seed data for local development
INSERT INTO personas (nombre, email, activo) VALUES
  ('Juan Pérez', 'juan@senati.pe', TRUE),
  ('María García', 'maria@senati.pe', TRUE),
  ('Carlos López', 'carlos@senati.pe', TRUE)
ON CONFLICT (email) DO NOTHING;
