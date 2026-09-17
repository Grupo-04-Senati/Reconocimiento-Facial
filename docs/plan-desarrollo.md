# Plan de Desarrollo

## Fases del Proyecto

### Fase 1: MVP (Semanas 1-2)
- [x] Setup del proyecto (repo, Supabase, CI/CD)
- [x] Frontend: Dashboard, navegación, cámara
- [x] Backend: API REST básica (health, personas)
- [x] Database: Migraciones y esquema base
- [ ] Testing básico

### Fase 2: Reconocimiento Facial (Semanas 3-4)
- [x] Integrar InsightFace + ArcFace
- [x] Endpoint de reconocimiento
- [x] Búsqueda vectorial con pgvector
- [x] Función RPC match_face_embedding
- [ ] Optimización de rendimiento

### Fase 3: Probabilidades (Semanas 5-6)
- [x] Modelo de calibración
- [x] Endpoint de predicción
- [x] Gráficos de historial
- [x] Métricas y estadísticas
- [ ] Interfaz de ajuste de umbrales

### Fase 4: Machine Learning (Semanas 7-8)
- [x] Pipeline de entrenamiento
- [x] Calibración isotónica
- [x] Métricas de evaluación
- [ ] Dataset etiquetado
- [ ] Modelo entrenado en producción

### Fase 5: Producción (Semanas 9-10)
- [x] Docker Compose
- [x] GitHub Actions CI/CD
- [x] Documentación completa
- [ ] Deploy a servidor
- [ ] Monitoreo (Prometheus + Grafana)
- [ ] Auditoría y compliance

## Equipo

| Rol | Responsabilidad |
|-----|----------------|
| Arquitecto | Diseño de sistema, stack tecnológico |
| Backend Dev | API, servicios, ML pipeline |
| Frontend Dev | UI/UX, componentes React |
| DevOps | CI/CD, Docker, deploy |
| Data Engineer | Migraciones, pgvector, datos |
