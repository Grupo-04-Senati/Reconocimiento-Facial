# Sistema Inteligente de Reconocimiento Facial y Análisis de Probabilidades

> Proyecto de IA, Machine Learning y Deep Learning - Grupo 04 Senati

## Descripción

Sistema completo de reconocimiento facial que utiliza redes neuronales profundas (ArcFace/InsightFace) para la extracción de embeddings faciales, búsqueda vectorial con pgvector, y modelos de machine learning para la calibración de probabilidades de coincidencia.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| ML/DL | InsightFace (ArcFace) + scikit-learn |
| Base de Datos | PostgreSQL 16 + pgvector |
| Auth & Storage | Supabase |
| CI/CD | GitHub Actions |
| Contenedores | Docker + Docker Compose |

## Inicio Rápido

### Requisitos

- Node.js >= 20.x
- Python >= 3.11
- Docker (opcional)
- Supabase CLI (opcional)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Grupo-04-Senati/Reconocimiento-Facial.git
cd Reconocimiento-Facial

# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### Configurar Variables de Entorno

```bash
# Copiar plantilla
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Editar con tus credenciales de Supabase
```

### Ejecutar

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Supabase Studio**: http://localhost:54323

## Estructura del Proyecto

```
Reconocimiento-Facial/
├── frontend/          # React + TypeScript + Vite
├── backend/           # FastAPI + Python
├── database/          # Migraciones SQL
├── supabase/          # Config Supabase
├── infra/             # Docker, K8s, Monitoring
├── docs/              # Documentación
├── scripts/           # Scripts de setup
├── .github/           # CI/CD y templates
└── docker-compose.yml
```

## Documentación

- [Arquitectura](docs/arquitectura.md)
- [Referencia API](docs/api-reference.md)
- [ML Pipeline](docs/ml-pipeline.md)
- [Seguridad y Privacidad](docs/seguridad-privacidad.md)
- [Plan de Desarrollo](docs/plan-desarrollo.md)
- [Manual de Usuario](docs/manual-usuario.md)
- [Setup Supabase](docs/supabase-setup.md)

## Licencia

MIT License - Grupo 04 Senati 2026
