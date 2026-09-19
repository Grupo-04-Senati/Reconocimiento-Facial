# Seguridad y Privacidad

## Ley N.° 29733 - Protección de Datos Personales (Perú)

Este sistema cumple con los principios fundamentales de la Ley N.° 29733:

### Principios Implementados

1. **Consentimiento**: Los usuarios deben autorizar el registro de su rostro
2. **Finalidad**: Los datos solo se usan para reconocimiento facial
3. **Proporcionalidad**: Solo se almacenan embeddings (no imágenes originales en BD)
4. **Calidad**: Validación de calidad de imagen antes del registro
5. **Seguridad**: Cifrado en tránsito (HTTPS) y en reposo
6. **Disponibilidad**: Backup y recuperación de datos
7. **Responsabilidad**: Auditoría de todos los accesos

### Derechos del Titular

- Derecho de acceso a sus datos
- Derecho de rectificación
- Derecho de eliminación (right to be forgotten)
- Derecho de oposición al tratamiento

## Medidas de Seguridad Técnicas

| Medida | Implementación |
|--------|---------------|
| Autenticación | JWT + Supabase Auth |
| Autorización | Row Level Security (RLS) |
| Cifrado en tránsito | HTTPS (producción) |
| Cifrado en reposo | Supabase Encryption |
| Gestión de secretos | .env + GitHub Secrets |
| Auditoría | recognition_logs + audit_service |
| Rate Limiting | Configurable por endpoint |
| Validación de entrada | Pydantic schemas |

## Datos Sensibles

| Dato | Almacenamiento | Acceso |
|------|---------------|--------|
| Embedding facial (512d) | PostgreSQL (pgvector) | service_role only |
| Imágenes faciales | Supabase Storage (bucket privado) | service_role only |
| Email | PostgreSQL | authenticated + admin |
| Logs de acceso | PostgreSQL | service_role + authenticated |

## Buenas Prácticas

- NUNCA commitear credenciales en el repositorio
- NUNCA exponer `SUPABASE_SERVICE_ROLE_KEY` al frontend
- NUNCA exponer embeddings en respuestas públicas
- Rotar JWT_SECRET periódicamente
- Activar 2FA en cuentas de administración
- Cambiar credenciales tras el primer login
