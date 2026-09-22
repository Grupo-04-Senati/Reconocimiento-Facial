-- Migración 012: etiqueta manual "tipo" en personas (real / ia)
--
-- Permite marcar cada persona registrada como 'real' (persona real) o 'ia'
-- (rostro generado por IA), para organizar y mostrar el dataset. Es una
-- etiqueta MANUAL (la asigna el admin), no una deteccion automatica.

ALTER TABLE personas
  ADD COLUMN IF NOT EXISTS tipo TEXT DEFAULT 'real';

COMMENT ON COLUMN personas.tipo IS 'Etiqueta manual: real (persona real) o ia (rostro generado por IA).';
