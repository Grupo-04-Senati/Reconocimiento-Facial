"""Punto de entrada para Vercel Serverless Functions.

Adapta la aplicación FastAPI al runtime de Vercel usando Mangum
(compatidor ASGI → Lambda/HTTP). En Vercel, el sistema de archivos
es read-only excepto /tmp, por lo que los modelos ONNX se descargan
desde Supabase Storage a /tmp/models/ bajo demanda.

Referencia: Sección 4 del PDF (Arquitectura tecnológica - Backend Python/FastAPI)
"""
import os
import sys

# Añadir backend/ al path para que 'from app.xxx' funcione
# Vercel ejecuta desde la raíz del repo
_backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from mangum import Mangum
from app.main import app

# Mangum adapta FastAPI (ASGI) al runtime Lambda de Vercel
handler = Mangum(app, lifespan="auto")
