"""
Punto de entrada para Vercel Serverless Functions.

Vercel detecta este archivo via vercel.json → builds → backend/api/index.py.
Expone la variable `app` (FastAPI) para que Vercel la sirva como API.

Referencia PDF:
- Sección 4: Backend Python 3.11 + FastAPI
- Sección 10: API REST desplegada en Vercel
"""
import os
import sys
import logging

# Configurar logging básico para diagnóstico en Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir backend/ al sys.path para que 'from app.xxx' funcione.
# Vercel ejecuta desde la raíz del repo, así que backend/ es un subdirectorio.
_backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

logger.info(f"sys.path includes: {_backend_dir}")

try:
    from app.main import app
    logger.info("FastAPI app imported successfully")
except ImportError as e:
    logger.error(f"Failed to import app.main: {e}")
    logger.error(f"sys.path: {sys.path}")
    # Crear una app de fallback que al menos devuelva un error claro
    from fastapi import FastAPI
    app = FastAPI(title="Facial Recognition API (ERROR)")

    @app.get("/api/health")
    async def health_error():
        return {
            "status": "error",
            "message": f"Import error: {str(e)}",
            "sys_path": sys.path[:5],
        }
except Exception as e:
    logger.error(f"Unexpected error importing app: {e}")
    from fastapi import FastAPI
    app = FastAPI(title="Facial Recognition API (ERROR)")

    @app.get("/api/health")
    async def health_error():
        return {"status": "error", "message": str(e)}
