"""
Punto de entrada para Vercel Serverless Functions.

Vercel detecta este archivo via vercel.json builds -> backend/api/index.py.
Expone la variable `app` (FastAPI) para que Vercel la sirva como API.

Referencia: Seccion 4 del PDF (Backend Python/FastAPI en Vercel)
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# backend/api/index.py -> backend/ para imports de app.xxx
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

logger.info(f"Vercel entry point loaded. sys.path[0]={sys.path[0]}")

try:
    from app.main import app
    logger.info("FastAPI app imported successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error(f"sys.path: {sys.path[:8]}")
    from fastapi import FastAPI
    app = FastAPI(title="Facial Recognition API (IMPORT ERROR)")

    @app.get("/api/health")
    async def health_error():
        return {"status": "error", "message": f"Import error: {str(e)}"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    from fastapi import FastAPI
    app = FastAPI(title="Facial Recognition API (ERROR)")

    @app.get("/api/health")
    async def health_error():
        return {"status": "error", "message": str(e)}
