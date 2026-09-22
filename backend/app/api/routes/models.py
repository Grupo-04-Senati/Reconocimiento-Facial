from __future__ import annotations
from fastapi import APIRouter, HTTPException, Body, Depends, UploadFile, File, Form
from app.core.logging_config import logger
from app.core.config import get_settings
from app.api.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/api/modelos", tags=["models"])
settings = get_settings()


def _get_supabase():
    try:
        from app.core.supabase_client import supabase_admin
        if supabase_admin is not None:
            return supabase_admin
    except Exception as e:
        print(f"[models] supabase import error: {e}")
    return None


@router.get("/status")
async def model_status(user: dict = Depends(get_current_user)):
    try:
        supabase_status = "no disponible"
        try:
            sb = _get_supabase()
            if sb is not None:
                sb.table("personas").select("id").limit(1).execute()
                supabase_status = "conectado"
        except Exception as e:
            print(f"[status] Supabase error: {e}")
            supabase_status = f"error: {str(e)[:100]}"

        face_status = "no disponible"
        try:
            from app.services.face_service import face_service
            face_status = "cargado" if face_service._initialized else "lazy (no cargado)"
        except Exception as e:
            print(f"[status] Face service error: {e}")
            face_status = f"error: {str(e)[:100]}"

        prob_status = "no disponible"
        try:
            from app.services.probability_service import probability_service
            prob_status = "cargado" if probability_service.model is not None else "lazy (no cargado)"
        except Exception as e:
            print(f"[status] Probability service error: {e}")
            prob_status = f"error: {str(e)[:100]}"

        return {
            "success": True,
            "supabase": supabase_status,
            "models": {
                "face_detection": face_status,
                "probability": prob_status,
            },
        }
    except Exception as e:
        print(f"[status] Error general: {e}")
        return {
            "success": False,
            "supabase": "error",
            "error": str(e)[:200],
        }


@router.post("/entrenar")
async def entrenar_modelo(user: dict = Depends(get_current_admin)):
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    # Modelo unificado: 9 features (similitud + OpenCV) desde ml_training_records + ml_face_samples
    try:
        from app.ml.trainer import train_model
        metrics = train_model()
        if metrics is not None:
            from app.services.probability_service import probability_service
            probability_service.reload()
            import json
            try:
                metrics_path = settings.ML_MODEL_PATH.replace(".joblib", "_metrics.json")
                with open(metrics_path, "w") as f:
                    json.dump(metrics, f)
            except Exception:
                pass
            return {
                "success": True,
                "message": "Modelo unificado entrenado (9 features: similitud + OpenCV)",
                "records_used": metrics.get("n_records", 0),
                "metrics": metrics,
                "detailed_metrics": metrics,
            }
    except Exception as e:
        logger.warning(f"entrenar (unificado) fallo: {e}")

    raise HTTPException(
        status_code=400,
        detail="No hay suficientes registros de ambas clases (Humano Real y No Real). "
               "Registra personas o confirma resultados en el Historial para generar datos.",
    )


@router.get("/metricas")
async def obtener_metricas(user: dict = Depends(get_current_user)):
    try:
        import os
        import joblib
        import httpx as _hx

        records_count = 0
        positive_count = 0
        negative_count = 0
        kaggle_count = 0

        # PostgREST directo (el SDK tiene count="exact" roto)
        try:
            h = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}
            # Contar todos los ml_training_records
            r_all = _hx.get(f"{settings.SUPABASE_URL}/rest/v1/ml_training_records",
                           params={"select": "resultado_real"}, headers=h, timeout=30)
            if r_all.status_code == 200:
                rows = r_all.json() or []
                records_count = len(rows)
                for row in rows:
                    val = row.get("resultado_real")
                    if val is True or val == "true" or val == "True" or val == 1:
                        positive_count += 1
                    elif val is False or val == "false" or val == "False" or val == 0:
                        negative_count += 1
        except Exception as e:
            print(f"[metricas] Error counting ml_training_records: {e}")

        # Contar ml_face_samples por separado (solo informativo)
        try:
            h = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}
            fs_resp = _hx.get(f"{settings.SUPABASE_URL}/rest/v1/ml_face_samples",
                              params={"select": "es_real"}, headers=h, timeout=30)
            if fs_resp.status_code == 200:
                fs_rows = fs_resp.json() or []
                kaggle_count = len(fs_rows)
        except Exception as e:
            print(f"[metricas] Error counting ml_face_samples: {e}")

        # Modelo unificado (9 features: similitud + OpenCV)
        trained = os.path.exists(settings.ML_MODEL_PATH)
        if not trained:
            model_info_str = "No hay modelo"
        else:
            try:
                data = joblib.load(settings.ML_MODEL_PATH)
                if isinstance(data, dict):
                    model_info_str = data.get("model_type", "unknown")
                else:
                    model_info_str = type(data).__name__
            except Exception:
                model_info_str = "unknown"

        # Contar registros por fuente
        fuente_counts = {}
        try:
            import httpx as _hx
            h = {"apikey": settings.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"}
            r = _hx.get(f"{settings.SUPABASE_URL}/rest/v1/ml_training_records",
                        params={"select": "fuente"}, headers=h, timeout=30)
            if r.status_code == 200:
                for row in (r.json() or []):
                    f = row.get("fuente") or "sistema"
                    fuente_counts[f] = fuente_counts.get(f, 0) + 1
        except Exception:
            pass

        try:
            import json
            metrics_path = settings.ML_MODEL_PATH.replace(".joblib", "_metrics.json")
            saved_metrics = None
            if os.path.exists(metrics_path):
                with open(metrics_path) as f:
                    saved_metrics = json.load(f)
        except Exception:
            saved_metrics = None

        return {
            "success": True,
            "trained": trained,
            "model_class": model_info_str,
            "model_path": settings.ML_MODEL_PATH,
            "kaggle_count": kaggle_count,
            "fuente_counts": fuente_counts,
            "metrics": saved_metrics or {
                "model_type": model_info_str,
                "features": ["similitud", "distancia", "calidad_imagen", "iluminacion", "textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura", "asimetria", "brillo_variacion", "edge_consistency", "fft_varianza", "freq_edge_mean", "freq_edge_var", "lbp_mean", "lbp_var", "lbp_contraste", "entropy", "skin_smoothness"],
                "threshold": settings.UMBRAL_SIMILITUD,
                "n_records": records_count,
                "positivos": positive_count,
                "negativos": negative_count,
            },
            "detailed_metrics": saved_metrics or {
                "n_records": records_count,
                "positivos": positive_count,
                "negativos": negative_count,
                "kaggle": kaggle_count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo metricas")


@router.get("/clasificacion")
async def clasificacion_personas(user: dict = Depends(get_current_user)):
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    try:
        result = sb.table("recognition_logs").select(
            "id, persona_id, similitud, distancia, umbral, coincide, resultado_real, probabilidad_calibrada, created_at, personas(nombre, email)"
        ).execute()
        logs = result.data or []

        from app.services.probability_service import probability_service
        umbral_dec = probability_service.umbral_decision

        confirmed = []
        for log in logs:
            rr = log.get("resultado_real")
            if rr is True or rr == "true" or rr == "True" or rr == 1:
                log["resultado_real"] = True
                confirmed.append(log)
            elif rr is False or rr == "false" or rr == "False" or rr == 0:
                log["resultado_real"] = False
                confirmed.append(log)

        vp = []
        fn = []
        fp = []
        tn = []

        for log in confirmed:
            is_real = log["resultado_real"]
            prob = log.get("probabilidad_calibrada")
            predicted_real = prob >= umbral_dec if prob is not None else log.get("coincide", False)
            persona = log.get("personas") or {}
            persona_nombre = persona.get("nombre", "Desconocido")
            persona_email = persona.get("email", "")
            persona_id = log.get("persona_id", "")
            entry = {
                "persona_id": persona_id,
                "nombre": persona_nombre,
                "email": persona_email,
                "similitud": round(log.get("similitud", 0) * 100, 1),
                "distancia": round(log.get("distancia", 0), 4),
                "fecha": log.get("created_at", ""),
            }

            if is_real and predicted_real:
                vp.append(entry)
            elif is_real and not predicted_real:
                fn.append(entry)
            elif not is_real and predicted_real:
                fp.append(entry)
            elif not is_real and not predicted_real:
                tn.append(entry)

        return {
            "success": True,
            "humanos_reales": vp,
            "humanos_semi_reales": fn,
            "no_reales_detectados": fp,
            "no_reales_rechazados": tn,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail="Error clasificando personas")


@router.post("/recalcular-resultado")
async def recalcular_resultado_real(user: dict = Depends(get_current_admin)):
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    try:
        import httpx
        # select("*") evita error si calidad_imagen/iluminacion aun no existen
        # (migracion 011); los valores faltantes se completan con .get() abajo.
        result = sb.table("recognition_logs").select("*").execute()
        logs = result.data or []

        from app.services.probability_service import probability_service

        rest_url = f"{settings.SUPABASE_URL}/rest/v1/recognition_logs"
        rest_headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        updated = 0
        for log in logs:
            features = {
                "similitud": log.get("similitud") or 0,
                "distancia": log.get("distancia") or 1.0,
                "calidad_imagen": log.get("calidad_imagen") or 0.5,
                "iluminacion": log.get("iluminacion") or 0.5,
                "textura": log.get("textura") or 0.5,
                "frecuencia_baja": log.get("frecuencia_baja") or 0.5,
                "frecuencia_alta": log.get("frecuencia_alta") or 0.5,
                "ruido": log.get("ruido") or 0.5,
                "contraste_textura": log.get("contraste_textura") or 0.5,
                "asimetria": log.get("asimetria") or 0.5,
                "brillo_variacion": log.get("brillo_variacion") or 0.5,
                "edge_consistency": log.get("edge_consistency") or 0.5,
                "fft_varianza": log.get("fft_varianza") or 0.5,
                "freq_edge_mean": log.get("freq_edge_mean") or 0.5,
                "freq_edge_var": log.get("freq_edge_var") or 0.5,
                "lbp_mean": log.get("lbp_mean") or 0.5,
                "lbp_var": log.get("lbp_var") or 0.5,
                "lbp_contraste": log.get("lbp_contraste") or 0.5,
                "entropy": log.get("entropy") or 0.5,
                "skin_smoothness": log.get("skin_smoothness") or 0.5,
            }
            try:
                prob = probability_service.predecir(features)
                predicted_real = prob >= probability_service.umbral_decision
            except Exception:
                predicted_real = log.get("coincide", False)

            old_rr = log.get("resultado_real")
            old_bool = None
            if old_rr is True or old_rr == "true" or old_rr == "True" or old_rr == 1:
                old_bool = True
            elif old_rr is False or old_rr == "false" or old_rr == "False" or old_rr == 0:
                old_bool = False

            if old_bool != predicted_real:
                try:
                    async with httpx.AsyncClient() as cl:
                        await cl.patch(
                            rest_url,
                            json={"resultado_real": predicted_real},
                            headers=rest_headers,
                            params={"id": f"eq.{log['id']}"},
                            timeout=15,
                        )
                    updated += 1
                except Exception:
                    pass

        return {
            "success": True,
            "message": f"{updated} registros actualizados de {len(logs)} total",
            "total": len(logs),
            "updated": updated,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recalculate error: {e}")
        raise HTTPException(status_code=500, detail="Error recalculando resultados")


@router.post("/limpiar-db")
async def limpiar_base_datos(data: dict = Body(default={}), user: dict = Depends(get_current_admin)):
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    try:
        import httpx
        todo = data.get("todo", False)

        rest_headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        def count_result(data_obj):
            return data_obj.count or 0 if hasattr(data_obj, 'count') else 0

        logs_count = count_result(sb.table("recognition_logs").select("id", count="exact").execute())
        ml_count = count_result(sb.table("ml_training_records").select("id", count="exact").execute())
        samples_count = 0
        try:
            r = sb.table("ml_face_samples").select("id", count="exact").execute()
            samples_count = r.count or 0
        except Exception:
            pass
        if samples_count == 0:
            try:
                r2 = sb.table("ml_face_samples").select("id").limit(1).execute()
                if r2.data and len(r2.data) > 0:
                    samples_count = 999
            except Exception:
                pass
        emb_count = 0
        pers_count = 0
        if todo:
            emb_count = count_result(sb.table("face_embeddings").select("id", count="exact").execute())
            pers_count = count_result(sb.table("personas").select("id", count="exact").execute())

        tables_to_delete = []
        if logs_count > 0:
            tables_to_delete.append("recognition_logs")
        if ml_count > 0:
            tables_to_delete.append("ml_training_records")
        if samples_count > 0:
            tables_to_delete.append("ml_face_samples")
        if todo:
            if emb_count > 0:
                tables_to_delete.append("face_embeddings")
            if pers_count > 0:
                tables_to_delete.append("personas")

        for table_name in tables_to_delete:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.delete(
                        f"{settings.SUPABASE_URL}/rest/v1/{table_name}",
                        headers=rest_headers,
                        params={"id": "neq.00000000-0000-0000-0000-000000000000"},
                        timeout=30,
                    )
                if resp.status_code not in (200, 204):
                    logger.error(f"Delete {table_name} error: {resp.status_code} {resp.text[:200]}")
            except Exception as e:
                logger.error(f"Delete {table_name} exception: {e}")

        try:
            import os
            for p in (settings.ML_MODEL_PATH, settings.EMB_MODEL_PATH):
                if os.path.exists(p):
                    os.remove(p)
            metrics_path = settings.ML_MODEL_PATH.replace(".joblib", "_metrics.json")
            if os.path.exists(metrics_path):
                os.remove(metrics_path)
        except Exception:
            pass

        # Limpia el modelo en memoria (queda sin clasificar hasta reentrenar).
        try:
            from app.services.probability_service import probability_service
            probability_service.reload()
        except Exception:
            pass

        msg = f"Limpiado: {logs_count} logs, {ml_count} training records, {samples_count} muestras embedding"
        if todo:
            msg += f", {emb_count} embeddings, {pers_count} personas"
        msg += ". Modelo ML eliminado."

        return {
            "success": True,
            "message": msg,
            "recognition_logs_deleted": logs_count,
            "ml_training_records_deleted": ml_count,
            "personas_deleted": pers_count,
            "embeddings_deleted": emb_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clean DB error: {e}")
        raise HTTPException(status_code=500, detail="Error limpiando la base de datos")


@router.post("/agregar-muestra")
async def agregar_muestra(
    imagen: UploadFile = File(...),
    resultado_real: bool = True,
    nombre: str = Form(""),
    email: str = Form(""),
    user: dict = Depends(get_current_admin),
):
    """Carga masiva UNIFICADA: registra la persona (embedding + log) y ademas
    guarda la muestra de entrenamiento etiquetada, en una sola accion.

    Asi todo aparece en tiempo real (personas, 1:N, historial) y el ML tiene datos.
    - resultado_real=True  -> tipo 'real', ejemplo Humano Real (positivo)
    - resultado_real=False -> tipo 'ia',  ejemplo No Real (negativo)
    La similitud se calcula contra los YA registrados: subir varias fotos de la
    misma persona real da similitud alta (senal util para el ML).
    """
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    from app.services.face_service import face_service
    if not face_service._initialized:
        raise HTTPException(status_code=503, detail="Modelo IA no disponible. Intenta de nuevo.")

    try:
        import time
        image_bytes = await imagen.read()
        face_data = face_service.get_embedding_with_quality(image_bytes)  # ValueError si no hay rostro
        embedding = face_data["embedding"]
        quality = face_data["quality"]
        illum = face_data["illumination"]

        # Similitud vs los YA registrados (antes de agregar esta)
        from app.ml.vector_store import vector_store
        matches = vector_store.search_similar(query_embedding=embedding, threshold=0.0, match_count=1)
        similitud = float(matches[0]["similitud"]) if matches else 0.0
        distancia = float(matches[0]["distancia"]) if matches else 1.0

        # 1) Registrar la persona (para que aparezca en todas las paginas)
        tipo_val = "real" if resultado_real else "ia"
        stamp = int(time.time() * 1000)
        nombre_final = (nombre or "").strip() or f"Persona {stamp}"
        email_final = (email or "").strip() or f"carga_{stamp}@dataset.local"
        payload = {"nombre": nombre_final, "email": email_final, "activo": True, "tipo": tipo_val}
        try:
            persona = sb.table("personas").insert(payload).execute()
        except Exception:
            payload.pop("tipo", None)
            persona = sb.table("personas").insert(payload).execute()
        persona_id = persona.data[0]["id"] if persona.data else None

        # 2) Guardar el embedding
        emb_list = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        if persona_id:
            sb.table("face_embeddings").insert({
                "persona_id": str(persona_id), "embedding": emb_list, "modelo": "buffalo_s",
            }).execute()

        # 3) Log de reconocimiento (aparece en Historial)
        from app.services.audit_service import audit_service
        try:
            audit_service.log_recognition(
                persona_id=str(persona_id) if persona_id else None,
                similitud=similitud, distancia=distancia, umbral=settings.UMBRAL_SIMILITUD,
                coincide=similitud >= settings.UMBRAL_SIMILITUD, probabilidad_calibrada=None,
                calidad_imagen=quality, iluminacion=illum,
                resultado_real=resultado_real,  # queda ya confirmado (no pendiente)
            )
        except Exception as e:
            logger.warning(f"agregar_muestra: log_recognition fallo: {e}")

        # 4) Muestra de entrenamiento con las 21 features REALES (no dummy 0.5).
        # face_data ya trae textura, LBP, FFT, entropia, skin_smoothness, etc.
        feats = {
            "similitud": similitud, "distancia": distancia,
            "calidad_imagen": quality, "iluminacion": illum,
            "embedding": embedding, "fuente": "manual",
        }
        for k in ("textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura",
                  "asimetria", "brillo_variacion", "edge_consistency", "fft_varianza",
                  "freq_edge_mean", "freq_edge_var", "lbp_mean", "lbp_var", "lbp_contraste",
                  "entropy", "skin_smoothness"):
            if face_data.get(k) is not None:
                feats[k] = face_data[k]
        audit_service.log_training_record(features=feats, resultado_real=resultado_real)

        # 5) Muestra por EMBEDDING (para el clasificador Real vs IA por pixeles).
        # Best-effort: si la tabla no existe (migracion 013), no rompe la carga.
        try:
            sb.table("ml_face_samples").insert({
                "embedding": emb_list, "es_real": resultado_real, "fuente": "manual",
            }).execute()
        except Exception as e:
            logger.warning(f"agregar_muestra: ml_face_samples insert fallo: {e}")

        return {
            "success": True,
            "persona_id": persona_id,
            "resultado_real": resultado_real,
            "clase": "Humano Real" if resultado_real else "No Real",
            "similitud": round(similitud, 4),
        }
    except ValueError as e:
        # No se detecto un rostro -> no sirve
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"agregar_muestra error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.post("/muestra-embedding")
async def muestra_embedding(
    imagen: UploadFile = File(...),
    es_real: bool = True,
    fuente: str = "kaggle",
    user: dict = Depends(get_current_admin),
):
    """Guarda SOLO una muestra de entrenamiento por embedding (Real vs IA), sin
    registrar persona. Es la via 'interna' para el dataset de Kaggle: cada imagen
    -> rostro -> embedding 512 -> ml_face_samples(es_real). No aparece en registros
    ni en 1:N; solo entrena el clasificador por pixeles.
    """
    sb = _get_supabase()
    if sb is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")
    from app.services.face_service import face_service
    if not face_service._initialized:
        raise HTTPException(status_code=503, detail="Modelo IA no disponible. Intenta de nuevo.")
    try:
        image_bytes = await imagen.read()
        face_data = face_service.get_embedding_with_quality(image_bytes)  # ValueError si no hay rostro
        embedding = face_data["embedding"]
        emb_list = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        fuente_val = (fuente or "kaggle")[:32]

        # (a) Embedding (para el clasificador por embedding, opcional). Best-effort.
        try:
            sb.table("ml_face_samples").insert({
                "embedding": emb_list, "es_real": bool(es_real), "fuente": fuente_val,
            }).execute()
        except Exception as e:
            logger.warning(f"muestra_embedding: ml_face_samples insert fallo: {e}")

        # (b) Registro de entrenamiento con las 21 features REALES calculadas de la
        # imagen, para que el modelo UNIFICADO (21 features) SI use Kaggle. Sin esto,
        # Kaggle no aparece en la matriz. No crea persona (queda como dato interno).
        from app.services.audit_service import audit_service
        feats = {
            "similitud": 0.0, "distancia": 1.0,
            "calidad_imagen": face_data.get("quality", 0.5),
            "iluminacion": face_data.get("illumination", 0.5),
            "embedding": embedding, "fuente": fuente_val,
        }
        for k in ("textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura",
                  "asimetria", "brillo_variacion", "edge_consistency", "fft_varianza",
                  "freq_edge_mean", "freq_edge_var", "lbp_mean", "lbp_var", "lbp_contraste",
                  "entropy", "skin_smoothness"):
            if face_data.get(k) is not None:
                feats[k] = face_data[k]
        audit_service.log_training_record(features=feats, resultado_real=bool(es_real))

        return {
            "success": True,
            "es_real": bool(es_real),
            "clase": "Humano Real" if es_real else "No Real (IA)",
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))  # sin rostro detectable
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"muestra_embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")
