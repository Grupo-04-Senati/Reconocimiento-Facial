# Backend - Sistema de Reconocimiento Facial

API REST construida con FastAPI para el sistema inteligente de reconocimiento facial.

## Desarrollo

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000

# Documentación
# Swagger: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## Testing

```bash
pytest tests/ -v
ruff check .
```
