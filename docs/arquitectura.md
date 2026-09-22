# Arquitectura del Sistema

## Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │Dashboard  │ │RegistroFacial│ │Reconocimiento│ │Probabilidades│ │
│  └────┬─────┘ └──────┬───────┘ └─────┬──────┘ └──────┬───────┘  │
│       └───────────────┴───────────────┴───────────────┘          │
│                           │ Axios / Supabase JS                  │
└───────────────────────────┼──────────────────────────────────────┘
                            │ HTTP REST API
┌───────────────────────────┼──────────────────────────────────────┐
│                      BACKEND (FastAPI)                            │
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────────┐   │
│  │  Health   │ │ Personas  │ │Reconocimiento│ │Probabilidades│   │
│  └──────────┘ └───────────┘ └──────┬──────┘ └──────┬───────┘   │
│                                     │               │            │
│  ┌──────────────────────────────────┴───────────────┴─────────┐  │
│  │                     SERVICES LAYER                         │  │
│  │  FaceService │ EmbeddingService │ ProbabilityService        │  │
│  │  StorageService │ AuditService                              │  │
│  └───────────────────────┬────────────────────────────────────┘  │
│                          │                                       │
│  ┌───────────────────────┴────────────────────────────────────┐  │
│  │                     ML PIPELINE                            │  │
│  │  InsightFace (ArcFace) │ scikit-learn │ Calibration        │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                     SUPABASE                                     │
│  ┌──────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────────┐   │
│  │PostgreSQL │ │    Auth    │ │   Storage   │ │   pgvector   │   │
│  │(personas, │ │  (JWT)    │ │(face-images)│ │  (embeddings)│   │
│  │ logs, ml) │ │           │ │             │ │              │   │
│  └──────────┘ └───────────┘ └─────────────┘ └──────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Flujo de Reconocimiento

1. **Captura**: Frontend captura imagen via webcam
2. **Envío**: Imagen enviada al backend via POST multipart
3. **Detección**: InsightFace detecta rostro y genera embedding (512d)
4. **Búsqueda**: pgvector busca embeddings similares (cosine distance)
5. **Calibración**: Modelo ML predice probabilidad calibrada
6. **Auditoría**: Resultado registrado en recognition_logs
7. **Respuesta**: Frontend muestra resultado con métricas

## Tecnologías

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React + TypeScript | 18.3 |
| Styling | Tailwind CSS | 3.4 |
| Build | Vite | 5.4 |
| Backend | FastAPI | 0.115 |
| ML/DL | InsightFace + ArcFace | 0.7.3 |
| ML | scikit-learn | 1.5 |
| DB | PostgreSQL + pgvector | 16 |
| Auth | Supabase Auth (JWT) | - |
| Storage | Supabase Storage | - |
