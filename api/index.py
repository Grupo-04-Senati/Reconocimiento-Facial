"""Punto de entrada para Vercel Serverless Functions.

CONVENCIÓN DE VERCEL:
  Las funciones serverless DEBEN estar en api/ en la RAÍZ del repo.
  NO en backend/api/ - Vercel no las detecta ahí.

Este archivo:
  1. Añade backend/ al sys.path
  2. Importa la app FastAPI desde app.main
  3. Usa Mangum como adaptador ASGI → Lambda/HTTP

Referencia: Sección 4 del PDF (Arquitectura tecnológica - Backend Python/FastAPI)
"""
import os
import sys

# Calcular la ruta al directorio backend/ (relativo a la raíz del repo)
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_backend_dir = os.path.join(_root_dir, "backend")

# Añadir backend/ al sys.path para que 'from app.xxx' funcione
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# También añadir la raíz por si hay imports relativos
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from mangum import Mangum
from app.main import app

# Mangum adapta FastAPI (ASGI) al runtime Lambda/HTTP de Vercel
# lifespan="auto" maneja startup/shutdown events
handler = Mangum(app, lifespan="auto")
