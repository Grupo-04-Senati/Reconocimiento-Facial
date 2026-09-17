# Supabase Setup

## Crear Proyecto en Nube

1. Ir a https://supabase.com/dashboard
2. Login con credenciales del equipo
3. Click **New Project**
4. Configurar:
   - Name: `reconocimiento-facial-senati`
   - Database Password: (generar segura)
   - Region: South America (São Paulo)
   - Pricing: Free
5. Esperar ~2 minutos

## Obtener Keys

En Settings → API:
- `SUPABASE_URL`: https://xxxxx.supabase.co
- `SUPABASE_ANON_KEY`: eyJ...
- `SUPABASE_SERVICE_ROLE_KEY`: eyJ...

En Settings → Database:
- `DATABASE_URL`: postgresql://postgres:[PASS]@db.xxxxx.supabase.co:5432/postgres

En Settings → Auth:
- `JWT_SECRET`: ...

## Vincular con Local

```bash
supabase init
supabase link --project-ref xxxxx
supabase db push
```

## Supabase Local (Docker)

```bash
supabase start
# Studio: http://localhost:54323
# API: http://localhost:54321
```

## Storage Bucket

Crear bucket `face-images`:
- Public: No
- File size limit: 5 MB
- Allowed MIME: image/jpeg, image/png, image/webp
