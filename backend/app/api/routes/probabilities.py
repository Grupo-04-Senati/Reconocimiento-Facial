import json
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional
import numpy as np
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/probabilidades", tags=["probabilities"])
settings = get_settings()


def _get_supabase():
    """Devuelve el cliente Supabase admin o None si no esta disponible."""
    try:
        from app.core.supabase_client import supabase_admin as sb
        if sb is not None:
            return sb
    except Exception as e:
        logger.warning(f"[probabilidades] supabase import error: {e}")
    return None


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")


class Comparar1NRequest(BaseModel):
    persona_id: str


class Comparar1A1Request(BaseModel):
    persona_a_id: str
    persona_b_id: str


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def _parse_embedding(raw):
    if isinstance(raw, str):
        raw = json.loads(raw)
    return np.array(raw, dtype=np.float32)


def _get_embedding_by_persona(persona_id: str):
    result = (
        supabase_admin.table("face_embeddings")
        .select("embedding")
        .eq("persona_id", persona_id)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    embs = [_parse_embedding(r["embedding"]) for r in rows]
    return np.mean(embs, axis=0)


def _get_all_personas_with_embeddings():
    # personas(*) trae 'tipo' si existe (migracion 012) y no rompe si no existe
    result = supabase_admin.table("face_embeddings").select(
        "persona_id, embedding, personas(*)"
    ).execute()
    rows = result.data or []
    person_map = {}
    for row in rows:
        pid = row["persona_id"]
        emb = _parse_embedding(row["embedding"])
        if pid not in person_map:
            info = row.get("personas") or {}
            person_map[pid] = {
                "id": pid,
                "nombre": info.get("nombre", ""),
                "email": info.get("email", ""),
                "tipo": info.get("tipo", "real"),
                "embeddings": [],
            }
        person_map[pid]["embeddings"].append(emb)
    return person_map


def _predecir_probabilidad(
    similitud: float,
    distancia: float,
    calidad_imagen: float = 1.0,
    iluminacion: float = 1.0,
) -> float:
    # calidad_imagen/iluminacion tienen default 1.0 para 1:N y 1:1 (vector vs vector,
    # sin imagen en vivo). En el modo Manual se pasan los valores reales de los sliders.
    try:
        from app.services.probability_service import probability_service
        return probability_service.predecir({
            "similitud": similitud,
            "distancia": distancia,
            "calidad_imagen": calidad_imagen,
            "iluminacion": iluminacion,
        })
    except Exception:
        return round(similitud * 0.7 + calidad_imagen * 0.15 + iluminacion * 0.15, 4)


# ─── 1:N: Seleccionar persona de BD, comparar contra TODAS ────────────────
@router.post("/comparar-1n")
async def comparar_1n(req: Comparar1NRequest, user: dict = Depends(get_current_user)):
    _check_supabase()

    persona_id = req.persona_id

    emb_origen = _get_embedding_by_persona(persona_id)
    if emb_origen is None:
        raise HTTPException(status_code=404, detail="Persona no tiene embeddings registrados")

    info_origen = supabase_admin.table("personas").select("id, nombre, email").eq("id", persona_id).execute()
    if not info_origen.data:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    person_map = _get_all_personas_with_embeddings()
    if not person_map:
        raise HTTPException(status_code=404, detail="No hay personas registradas")

    results = []
    for pid, pinfo in person_map.items():
        if pid == persona_id:
            continue

        best_sim = 0.0
        best_dist = 1.0
        for emb in pinfo["embeddings"]:
            sim = _cosine_similarity(emb_origen, emb)
            dist = 1.0 - sim
            if sim > best_sim:
                best_sim = sim
                best_dist = dist

        prob = _predecir_probabilidad(best_sim, best_dist)
        confianza = round(abs(prob - 0.5) * 2, 4)

        results.append({
            "persona_id": pid,
            "nombre": pinfo["nombre"],
            "email": pinfo["email"],
            "tipo": pinfo.get("tipo", "real"),
            "similitud": round(best_sim, 4),
            "distancia": round(best_dist, 4),
            "calidad_imagen": 1.0,
            "iluminacion": 1.0,
            "probabilidad_calibrada": prob,
            "confianza": confianza,
            "supera_umbral": best_sim >= settings.UMBRAL_SIMILITUD,
            "num_embeddings": len(pinfo["embeddings"]),
        })

    results.sort(key=lambda x: x["similitud"], reverse=True)

    persona_origen = info_origen.data[0]

    return {
        "success": True,
        "modo": "1:N",
        "umbral": settings.UMBRAL_SIMILITUD,
        "persona_origen": {
            "id": persona_id,
            "nombre": persona_origen["nombre"],
            "email": persona_origen.get("email", ""),
        },
        "total_comparaciones": len(results),
        "ranking": results,
    }


# ─── 1:1: Comparar 2 personas registradas entre si ────────────────────────
@router.post("/comparar-1a1")
async def comparar_1a1(req: Comparar1A1Request, user: dict = Depends(get_current_user)):
    _check_supabase()

    persona_a_id = req.persona_a_id
    persona_b_id = req.persona_b_id

    if persona_a_id == persona_b_id:
        raise HTTPException(status_code=400, detail="Selecciona dos personas diferentes")

    emb_a = _get_embedding_by_persona(persona_a_id)
    emb_b = _get_embedding_by_persona(persona_b_id)

    if emb_a is None:
        raise HTTPException(status_code=404, detail=f"Persona {persona_a_id} no tiene embeddings")
    if emb_b is None:
        raise HTTPException(status_code=404, detail=f"Persona {persona_b_id} no tiene embeddings")

    similitud = _cosine_similarity(emb_a, emb_b)
    distancia = 1.0 - similitud
    supera_umbral = similitud >= settings.UMBRAL_SIMILITUD
    prob = _predecir_probabilidad(similitud, distancia)
    confianza = round(abs(prob - 0.5) * 2, 4)

    info_a = supabase_admin.table("personas").select("id, nombre, email").eq("id", persona_a_id).execute()
    info_b = supabase_admin.table("personas").select("id, nombre, email").eq("id", persona_b_id).execute()

    return {
        "success": True,
        "modo": "1:1",
        "umbral": settings.UMBRAL_SIMILITUD,
        "persona_a": {
            "id": persona_a_id,
            "nombre": info_a.data[0]["nombre"] if info_a.data else "",
            "email": info_a.data[0].get("email", "") if info_a.data else "",
        },
        "persona_b": {
            "id": persona_b_id,
            "nombre": info_b.data[0]["nombre"] if info_b.data else "",
            "email": info_b.data[0].get("email", "") if info_b.data else "",
        },
        "similitud": round(similitud, 4),
        "distancia": round(distancia, 4),
        "calidad_imagen": 1.0,
        "iluminacion": 1.0,
        "probabilidad_calibrada": prob,
        "confianza": confianza,
        "supera_umbral": supera_umbral,
    }


# ─── Conteo de dataset para EntrenamientoML ────────────────────────────────
@router.get("/dataset-count")
async def dataset_count(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        positive = (
            supabase_admin.table("ml_training_records")
            .select("id", count="exact")
            .eq("resultado_real", True)
            .execute()
        )
        negative = (
            supabase_admin.table("ml_training_records")
            .select("id", count="exact")
            .eq("resultado_real", False)
            .execute()
        )
        pos_count = positive.count or 0
        neg_count = negative.count or 0
        if pos_count == 0 and neg_count == 0:
            all_records = supabase_admin.table("ml_training_records").select("resultado_real").execute()
            for r in (all_records.data or []):
                val = r.get("resultado_real")
                if val is True or val == "true" or val == "True" or val == 1:
                    pos_count += 1
                else:
                    neg_count += 1
        return {
            "success": True,
            "positivos": pos_count,
            "negativos": neg_count,
        }
    except Exception as e:
        logger.error(f"Dataset count error: {e}")
        return {"success": True, "positivos": 0, "negativos": 0}


# ─── Prediccion manual con sliders ─────────────────────────────────────────
class ManualPredictRequest(BaseModel):
    similitud: float
    calidad_imagen: float = 1.0
    iluminacion: float = 1.0


@router.post("/predecir-manual")
@router.post("/prediccion")
async def predecir_manual(req: ManualPredictRequest, user: dict = Depends(get_current_user)):
    distancia = 1.0 - req.similitud
    # Ahora sí usa la calidad e iluminacion de los sliders (antes se ignoraban)
    prob = _predecir_probabilidad(req.similitud, distancia, req.calidad_imagen, req.iluminacion)
    confianza = round(abs(prob - 0.5) * 2, 4)
    return {
        "success": True,
        "similitud": round(req.similitud, 4),
        "distancia": round(distancia, 4),
        "calidad_imagen": round(req.calidad_imagen, 4),
        "iluminacion": round(req.iluminacion, 4),
        "probabilidad_calibrada": prob,
        "confianza": confianza,
        "supera_umbral": req.similitud >= settings.UMBRAL_SIMILITUD,
        "umbral": settings.UMBRAL_SIMILITUD,
    }


# ─── Curva de sensibilidad ─────────────────────────────────────────────────
@router.get("/curva-sensibilidad")
async def curva_sensibilidad(user: dict = Depends(get_current_user)):
    points = []
    for sim_int in range(0, 101, 5):
        sim = sim_int / 100.0
        dist = 1.0 - sim
        prob = _predecir_probabilidad(sim, dist)
        points.append({
            "similitud": round(sim, 2),
            "distancia": round(dist, 2),
            "probabilidad": prob,
        })
    return {
        "success": True,
        "umbral": settings.UMBRAL_SIMILITUD,
        "points": points,
    }


# ─── Comparacion de escenarios (buena vs mala luz) ─────────────────────────
@router.get("/comparar-escenarios")
async def comparar_escenarios(user: dict = Depends(get_current_user)):
    results = []
    for sim_int in [20, 40, 50, 60, 70, 80, 90, 95]:
        sim = sim_int / 100.0
        dist = 1.0 - sim
        prob_buena = _predecir_probabilidad(sim, dist)
        results.append({
            "similitud": f"{sim_int}%",
            "buena_luz": prob_buena,
        })
    return {
        "success": True,
        "umbral": settings.UMBRAL_SIMILITUD,
        "escenarios": results,
    }


# ─── Info del modelo ML ────────────────────────────────────────────────────
@router.get("/modelo-info")
async def modelo_info(user: dict = Depends(get_current_user)):
    try:
        import os
        import joblib

        model = None
        model_class = None
        trained = False

        if os.path.exists(settings.ML_MODEL_PATH):
            try:
                data = joblib.load(settings.ML_MODEL_PATH)
                if isinstance(data, dict):
                    model = data.get("model", data)
                    model_class = data.get("model_type", type(model).__name__)
                else:
                    model = data
                    model_class = type(model).__name__
                trained = True
            except Exception as e:
                logger.warning(f"Error loading model file: {e}")

        sb = _get_supabase()
        total = 0
        pos = 0
        neg = 0
        if sb:
            try:
                r = sb.table("ml_training_records").select("id", count="exact").execute()
                total = r.count or 0
                p = sb.table("ml_training_records").select("id", count="exact").eq("resultado_real", True).execute()
                pos = p.count or 0
                n = sb.table("ml_training_records").select("id", count="exact").eq("resultado_real", False).execute()
                neg = n.count or 0
                if pos == 0 and neg == 0 and total > 0:
                    all_r = sb.table("ml_training_records").select("resultado_real").execute()
                    for rec in (all_r.data or []):
                        val = rec.get("resultado_real")
                        if val is True or val == "true" or val == "True" or val == 1:
                            pos += 1
                        else:
                            neg += 1
            except Exception:
                pass

        if not trained and pos >= 2 and neg >= 2:
            try:
                import numpy as np
                from app.ml.trainer import FaceTrainer
                result_all = sb.table("ml_training_records").select("*").execute()
                records = result_all.data or []
                if len(records) >= 4:
                    X = np.array([[r["similitud"], r["distancia"], r["calidad_imagen"], r["iluminacion"]] for r in records])
                    y = np.array([1 if r["resultado_real"] in (True, "true", "True", 1) else 0 for r in records])
                    trainer = FaceTrainer()
                    trainer.train(X, y)
                    trainer.save(settings.ML_MODEL_PATH)
                    trained = True
                    model_class = trainer.model_type
                    logger.info("Auto-retrained ML model in modelo-info")
            except Exception as e:
                logger.warning(f"Auto-retrain failed: {e}")

        feature_importance = None
        if model is not None:
            try:
                base = model
                if hasattr(base, 'estimator'):
                    base = base.estimator
                if hasattr(base, 'feature_importances_'):
                    feature_importance = {
                        "similitud": round(float(base.feature_importances_[0]), 4),
                        "distancia": round(float(base.feature_importances_[1]), 4),
                        "calidad_imagen": round(float(base.feature_importances_[2]), 4),
                        "iluminacion": round(float(base.feature_importances_[3]), 4),
                    }
                elif hasattr(base, 'coef_'):
                    coefs = base.coef_[0] if base.coef_.ndim > 1 else base.coef_
                    total_abs = sum(abs(c) for c in coefs)
                    if total_abs > 0:
                        feature_importance = {
                            "similitud": round(abs(coefs[0]) / total_abs, 4),
                            "distancia": round(abs(coefs[1]) / total_abs, 4),
                            "calidad_imagen": round(abs(coefs[2]) / total_abs, 4),
                            "iluminacion": round(abs(coefs[3]) / total_abs, 4),
                        }
            except Exception:
                pass

        return {
            "success": True,
            "trained": trained,
            "model_class": model_class,
            "n_records": total,
            "positivos": pos,
            "negativos": neg,
            "feature_importance": feature_importance,
            "pocos_datos": total < 50,
        }
    except Exception as e:
        logger.error(f"Model info error: {e}")
        return {"success": True, "trained": False, "message": str(e)[:200]}
