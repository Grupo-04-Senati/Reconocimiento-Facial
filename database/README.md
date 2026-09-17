# Database Migrations

## Archivos

| Archivo | Descripción |
|---|---|
| `000_enable_pgvector.sql` | Habilita extensiones pgvector y uuid-ossp |
| `001_create_personas.sql` | Tabla de personas registradas |
| `002_create_face_embeddings.sql` | Embeddings faciales vectoriales (512 dim) |
| `003_create_recognition_logs.sql` | Logs de reconocimiento |
| `004_create_ml_training_records.sql` | Registros de entrenamiento ML |

## Funciones RPC

- `match_face_embedding()` - Búsqueda vectorial por similitud coseno

## Políticas RLS

- `rls_personas.sql` - Row Level Security para personas
- `rls_face_embeddings.sql` - Acceso restringido a embeddings
- `retention_policy.sql` - Políticas de logs

## Aplicar migraciones

```bash
# Local
supabase db reset

# Nube
supabase db push
```
