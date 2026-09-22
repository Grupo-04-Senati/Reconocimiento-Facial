-- Migracion 010: Arreglar CHECK constraint en users.role
-- Ejecutar en Supabase SQL Editor

-- 1. Ver constraint actual
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'users'::regclass AND contype = 'c';

-- 2. Eliminar TODOS los CHECK constraints en la tabla users
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT conname FROM pg_constraint 
             WHERE conrelid = 'users'::regclass AND contype = 'c'
    LOOP
        EXECUTE 'ALTER TABLE users DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
        RAISE NOTICE 'Dropped: %', r.conname;
    END LOOP;
END $$;

-- 3. Crear el CHECK constraint correcto
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'operador', 'analista'));

-- 4. Verificar resultado
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'users'::regclass AND contype = 'c';
