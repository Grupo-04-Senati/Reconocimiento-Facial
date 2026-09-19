"""Punto de entrada Vercel Serverless Function.

Vercel detecta automaticamente api/index.py en la raiz.
Expone la variable `app` (FastAPI) para que Vercel la sirva.

Referencia: Seccion 4 del PDF (Backend Python/FastAPI en Vercel)
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# repo_root/api/index.py -> repo_root/backend/ para imports
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend_dir = os.path.join(_repo_root, "backend")

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

logger.info(f"Vercel entry point loaded. backend_dir={_backend_dir}")

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
