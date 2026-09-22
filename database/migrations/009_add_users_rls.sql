-- Migracion 009: Agregar RLS a tabla users
-- Ejecutar en Supabase SQL Editor si la tabla users no tiene RLS

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_service_role" ON users;
CREATE POLICY "users_service_role" ON users FOR ALL TO service_role USING (TRUE);
