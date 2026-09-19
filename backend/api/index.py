"""
Punto de entrada para Vercel Serverless Functions.

Vercel detecta este archivo via vercel.json builds -> backend/api/index.py.
La variable `app` DEBE estar en top-level (no dentro de try/except ni if).

Referencia: Seccion 4 del PDF (Backend Python/FastAPI en Vercel)
"""
import os
import sys

# backend/api/index.py -> backend/ para imports de app.xxx
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# IMPORT DIRECTO - sin try/except para que Vercel detecte 'app' en top-level
from app.main import app  # noqa: E402, F401
