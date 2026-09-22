# GitHub Workflow

## Flujo de Trabajo

```
main (protegida)
  └── develop
       ├── feature/fase-1-mvp
       ├── feature/fase-2-reconocimiento
       ├── feature/fase-3-probabilidades
       ├── feature/fase-4-ml
       └── feature/fase-5-produccion
```

## Proceso

1. Crear branch desde `develop`
2. Desarrollar funcionalidad
3. Push al branch feature
4. Crear Pull Request → `develop`
5. Code review + CI checks
6. Merge a `develop`
7. Cuando todo esté listo: PR `develop` → `main`

## Reglas

- `main` solo recibe merges desde `develop`
- Todo PR requiere al menos 1 aprobación
- CI debe pasar antes de merge
- No commitear directamente a `main`
- Usar commits convencionales: `feat:`, `fix:`, `chore:`, `docs:`

## GitHub Secrets

| Secret | Uso |
|--------|-----|
| `SUPABASE_URL` | URL de Supabase (nube) |
| `SUPABASE_ANON_KEY` | Anon key de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key |
| `DATABASE_URL` | Connection string PostgreSQL |
| `JWT_SECRET` | Secreto JWT |
