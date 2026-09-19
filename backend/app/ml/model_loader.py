"""Descarga y carga de modelos ONNX desde Supabase Storage.

Justificación (PDF Sección 4 y 5):
  - Modelo DL: InsightFace buffalo_l (SCRFD detección + ArcFace R100 embeddings)
  - Embedding: 512 dimensiones normalizadas (normed_embedding)
  - En Vercel, el filesystem es read-only excepto /tmp, por lo que los
    modelos se descargan de Supabase Storage a /tmp/models/ bajo demanda.

Estrategia de carga:
  1. Verificar si el modelo ya existe en /tmp/models/
  2. Si no existe, descargarlo desde Supabase Storage
  3. Cargar en memoria con lazy loading (solo cuando se necesita)
  4. Manejar errores de red o integridad
"""
import os
import hashlib
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

# Modelos que componen buffalo_l
BUFFALO_L_FILES = {
    "det_10g.onnx": "detección de rostros (SCRFD)",
    "w600k_r50.onnx": "embeddings faciales (ArcFace R100)",
    "2d106det.onnx": "landmarks faciales",
    "genderage.onnx": "estimación de género y edad",
}

_face_analysis_instance = None


def ensure_models_downloaded() -> bool:
    """Descarga los modelos ONNX a MODELS_DIR si no existen.

    Returns:
        True si todos los modelos están disponibles, False si falló alguno.
    """
    models_dir = settings.MODELS_DIR
    os.makedirs(models_dir, exist_ok=True)

    all_ok = True
    for filename, description in BUFFALO_L_FILES.items():
        filepath = os.path.join(models_dir, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            logger.info(f"Modelo existente: {filename} ({description})")
            continue

        logger.info(f"Descargando modelo: {filename} ({description})...")
        try:
            _download_from_supabase(filename, filepath)
            logger.info(f"Modelo descargado: {filename}")
        except Exception as e:
            logger.error(f"Error descargando {filename}: {e}")
            all_ok = False

    return all_ok


def _download_from_supabase(filename: str, dest_path: str) -> None:
    """Descarga un archivo desde Supabase Storage a una ruta local.

    Args:
        filename: Nombre del archivo en el bucket de modelos.
        dest_path: Ruta de destino en el sistema de archivos local.
    """
    from app.core.supabase_client import supabase_admin

    if supabase_admin is None:
        raise RuntimeError("Supabase no conectado. No se pueden descargar modelos.")

    bucket = settings.SUPABASE_MODELS_BUCKET
    response = supabase_admin.storage.from_(bucket).download(filename)

    with open(dest_path, "wb") as f:
        f.write(response)

    file_size = os.path.getsize(dest_path)
    if file_size < 1000:
        os.remove(dest_path)
        raise ValueError(f"Archivo descargado demasiado pequeño ({file_size} bytes)")


def get_face_analysis():
    """Obtiene la instancia de InsightFace FaceAnalysis con lazy loading.

    En Vercel, los modelos ya deben estar en /tmp/models/ antes de llamar.
    En desarrollo, InsightFace busca los modelos automáticamente.

    Returns:
        Instancia de FaceAnalysis lista para usar.

    Raises:
        RuntimeError: Si los modelos no están disponibles.
    """
    global _face_analysis_instance

    if _face_analysis_instance is not None:
        return _face_analysis_instance

    try:
        from insightface.app import FaceAnalysis
    except ImportError:
        raise RuntimeError(
            "insightface no instalado. Ejecuta: pip install insightface onnxruntime"
        )

    # En Vercel, configurar la ruta de modelos
    model_kwargs = {
        "providers": ["CPUExecutionProvider"],
    }

    if settings.IS_VERCEL:
        # InsightFace busca modelos en ~/.insightface/models/buffalo_l
        # En Vercel redirigimos a /tmp
        home_model_dir = os.path.expanduser("~/.insightface/models/buffalo_l")
        os.makedirs(home_model_dir, exist_ok=True)

        models_dir = settings.MODELS_DIR
        for filename in BUFFALO_L_FILES:
            src = os.path.join(models_dir, filename)
            dst = os.path.join(home_model_dir, filename)
            if os.path.exists(src) and not os.path.exists(dst):
                import shutil
                shutil.copy2(src, dst)

        model_kwargs["root"] = os.path.expanduser("~/.insightface")

    logger.info("Inicializando InsightFace FaceAnalysis (buffalo_l)...")
    fa = FaceAnalysis(name="buffalo_l", **model_kwargs)
    fa.prepare(ctx_id=0, det_size=(640, 640))

    _face_analysis_instance = fa
    logger.info("FaceAnalysis inicializado correctamente")
    return fa


def get_model_status() -> dict:
    """Retorna el estado de los modelos para el endpoint /api/modelos/status.

    Returns:
        Diccionario con el estado de cada modelo.
    """
    models_dir = settings.MODELS_DIR
    files_status = {}
    for filename, description in BUFFALO_L_FILES.items():
        filepath = os.path.join(models_dir, filename)
        exists = os.path.exists(filepath) and os.path.getsize(filepath) > 1000
        files_status[filename] = {
            "description": description,
            "available": exists,
            "path": filepath,
        }

    ml_model_exists = os.path.exists(settings.ML_MODEL_PATH)

    return {
        "face_models": files_status,
        "ml_model": {
            "available": ml_model_exists,
            "path": settings.ML_MODEL_PATH,
        },
        "models_dir": models_dir,
        "is_vercel": settings.IS_VERCEL,
    }
