"""
Aplicacion FastAPI - Sistema Inteligente de Reconocimiento Facial.
"""
import sys
import os
import asyncio
import time
from datetime import datetime, timezone
from functools import wraps

print("[main.py] Iniciando carga")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

print("[main.py] FastAPI importado OK")

app = FastAPI(
    title="Sistema Inteligente de Reconocimiento Facial",
    version="1.0.0",
    description="API de IA, ML y DL - Grupo 04 Senati",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://reconocimiento-facial-xi.vercel.app",
    "https://reconocimiento-facial-grupo-04-senati.vercel.app",
    "https://reconocimiento-facial-obe7k366m-grupo-04-senati.vercel.app",
    "https://reconocimiento-facial-pdv539api-grupo-04-senati.vercel.app",
]

try:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.CORS_ORIGINS:
        _cors_origins.extend(
            [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        )
    print(f"[main.py] Settings OK. ENV={settings.ENVIRONMENT}")
except Exception as e:
    print(f"[main.py] WARNING settings: {e}")
    settings = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://reconocimiento-facial-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

print("[main.py] CORS configurado")


_face_analysis = None


def get_face_analysis():
    global _face_analysis
    if _face_analysis is not None:
        return _face_analysis
    try:
        from insightface.app import FaceAnalysis
        model_root = "/root/.insightface"
        if not os.path.exists(os.path.join(model_root, "models", "buffalo_s")):
            model_root = None
        _face_analysis = FaceAnalysis(
            name="buffalo_s",
            root=model_root,
            providers=["CPUExecutionProvider"],
        )
        _face_analysis.prepare(ctx_id=0, det_size=(640, 640))
        print("[face] InsightFace buffalo_s loaded OK")
        return _face_analysis
    except Exception as e:
        print(f"[face] ERROR loading InsightFace: {e}")
        return None


def retry_on_dns_error(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if "name resolution" in str(e).lower() and attempt < max_retries - 1:
                        print(f"[retry] DNS error, attempt {attempt + 1}/{max_retries}")
                        await asyncio.sleep(delay * (attempt + 1))
                        continue
                    raise
        return wrapper
    return decorator


def _get_supabase():
    try:
        from app.core.supabase_client import supabase_admin
        if supabase_admin is not None:
            return supabase_admin
    except Exception as e:
        print(f"[supabase] import error: {e}")
    return None


@app.get("/api/debug")
async def debug():
    info = {
        "python": sys.version,
        "sys_path": sys.path[:5],
        "env_keys": sorted(os.environ.keys()),
        "modules": {},
    }
    for mod in ["fastapi", "insightface", "onnxruntime", "cv2", "numpy", "sklearn", "supabase"]:
        try:
            __import__(mod)
            info["modules"][mod] = "OK"
        except Exception as e:
            info["modules"][mod] = f"FAIL: {type(e).__name__}: {e}"
    return info


@app.get("/api")
async def api_root():
    return {
        "message": "Sistema de Reconocimiento Facial - Grupo 04 Senati",
        "docs": "/api/docs",
        "health": "/api/health",
        "debug": "/api/debug",
        "version": "1.0.0",
    }


@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS,PATCH",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Max-Age": "86400",
        },
    )


print("[main.py] Cargando routes...")
try:
    from app.api.routes import health as health_route
    from app.api.routes import personas
    from app.api.routes import recognition
    from app.api.routes import probabilities
    from app.api.routes import models
    from app.api.routes import auth
    from app.api.routes import dashboard
    app.include_router(health_route.router)
    app.include_router(personas.router)
    app.include_router(recognition.router)
    app.include_router(probabilities.router)
    app.include_router(models.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    print("[main.py] Routes cargadas OK")
except Exception as e:
    print(f"[main.py] ERROR cargando routes: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()


@app.on_event("startup")
async def startup_event():
    print("[startup] Backend arrancado. Modelos se cargan bajo demanda.")


@app.on_event("shutdown")
async def shutdown_event():
    print("[shutdown] Backend detenido.")
