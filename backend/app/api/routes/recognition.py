import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.supabase_client import supabase_admin, sb_update, sb_delete, sb_delete_all, sb_select_count
from app.core.config import get_settings
from app.core.logging_config import logger
from app.ml.vector_store import vector_store
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/reconocimiento", tags=["reconocimiento"])
settings = get_settings()

ML_FEATURE_KEYS = [
    "textura", "frecuencia_baja", "frecuencia_alta", "ruido", "contraste_textura",
    "asimetria", "brillo_variacion", "edge_consistency",
    "fft_varianza", "freq_edge_mean", "freq_edge_var",
    "lbp_mean", "lbp_var", "lbp_contraste", "entropy", "skin_smoothness",
]


def _build_features(match, face_data):
    return {
        "similitud": match["similitud"],
        "distancia": match["distancia"],
        "calidad_imagen": face_data["quality"],
        "iluminacion": face_data["illumination"],
        **{k: face_data.get(k) for k in ML_FEATURE_KEYS},
    }


def _build_features_from_log(log):
    return {
        "similitud": log.get("similitud") or 0,
        "distancia": log.get("distancia") or 1.0,
        "calidad_imagen": log.get("calidad_imagen") or 0.5,
        "iluminacion": log.get("iluminacion") or 0.5,
        **{k: log.get(k) or 0.5 for k in ML_FEATURE_KEYS},
    }


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase no conectado. Verifica la conexion a internet y las credenciales.",
        )


@router.post("")
async def reconocer(imagen: UploadFile = File(...), solo_prueba: bool = False, user: dict = Depends(get_current_user)):
    # solo_prueba=True: clasifica pero NO guarda log ni datos (para probar no-humanos
    # sin registrarlos como intentos "Desconocido" en el historial).
    _check_supabase()
    try:
        from app.services.face_service import face_service
        from app.services.audit_service import audit_service
        from app.services.probability_service import probability_service

        print(f"[reconocimiento] === INICIO ===")
        print(f"[reconocimiento] Modelo cargado: {face_service._initialized}")

        if not face_service._initialized:
            raise HTTPException(
                status_code=503,
                detail="Modelo IA no disponible. Intenta de nuevo en unos segundos.",
            )

        image_bytes = await imagen.read()
        print(f"[reconocimiento] Imagen: {len(image_bytes)} bytes")

        print(f"[reconocimiento] Paso 1: Obteniendo embedding...")
        face_data = face_service.get_embedding_with_quality(image_bytes)
        embedding = face_data["embedding"]

        print(f"[reconocimiento] Embedding: norm={np.linalg.norm(embedding):.4f}")

        print(f"[reconocimiento] Paso 2: Buscando en pgvector...")
        matches = vector_store.search_similar(
            query_embedding=embedding,
            threshold=0.0,
            match_count=5,
        )

        print(f"[reconocimiento] Matches: {len(matches)}")
        for i, m in enumerate(matches[:3]):
            print(f"  match {i}: persona_id={m.get('persona_id')}, similitud={m.get('similitud'):.4f}, nombre={m.get('nombre')}")

        coincide = bool(matches and matches[0]["similitud"] >= settings.UMBRAL_SIMILITUD)
        print(f"[reconocimiento] Umbral: {settings.UMBRAL_SIMILITUD}, Coincide: {coincide}")

        persona = None
        if coincide and matches:
            persona_id = matches[0]["persona_id"]
            nombre_match = matches[0].get("nombre")
            print(f"[reconocimiento] Buscando persona: {persona_id}")

            if nombre_match:
                persona = {"id": persona_id, "nombre": nombre_match, "email": None}
            else:
                try:
                    persona_result = supabase_admin.table("personas").select(
                        "id, nombre, email"
                    ).eq("id", persona_id).execute()
                    if persona_result.data:
                        persona = persona_result.data[0]
                except Exception as e:
                    print(f"[reconocimiento] Error consultando persona: {e}")

            if persona:
                print(f"[reconocimiento] Persona: {persona.get('nombre')} ({persona.get('email')})")

        # P(Humano Real): modelo unificado con 21 features
        prob = None
        umbral_prob = probability_service.umbral_decision

        match = {"similitud": matches[0]["similitud"] if matches else 0.0, "distancia": matches[0]["distancia"] if matches else 1.0}
        features = _build_features(match, face_data)

        if probability_service.model is not None:
            prob = probability_service.predecir(features)
            print(f"[reconocimiento] Probabilidad (modelo 12 features): {prob}")
        else:
            prob_emb = probability_service.predecir_embedding(embedding)
            if prob_emb is not None:
                prob = prob_emb
                umbral_prob = probability_service.umbral_embedding
                print(f"[reconocimiento] Probabilidad (embedding fallback): {prob}")
            elif matches:
                prob = probability_service._fallback_prediction(features)
                print(f"[reconocimiento] Probabilidad (fallback): {prob}")

        resultado_real = None
        clasificacion = None
        if prob is not None:
            predicted_real = prob >= umbral_prob
            resultado_real = predicted_real
            clasificacion = "humano_real" if predicted_real else "no_real"
        elif coincide:
            resultado_real = True
            clasificacion = "humano_real"

        print(f"[reconocimiento] Auto-clasificacion: {clasificacion} (prob={prob})")

        try:
            log_result = None if solo_prueba else audit_service.log_recognition(
                persona_id=str(persona["id"]) if persona else None,
                similitud=matches[0]["similitud"] if matches else 0.0,
                distancia=matches[0]["distancia"] if matches else 1.0,
                umbral=settings.UMBRAL_SIMILITUD,
                coincide=coincide,
                probabilidad_calibrada=prob,
                calidad_imagen=face_data["quality"],
                iluminacion=face_data["illumination"],
            )
            log_id = log_result.get("id") if log_result else None

            if log_id and resultado_real is not None:
                try:
                    import httpx
                    s = get_settings()
                    async with httpx.AsyncClient() as cl:
                        await cl.patch(
                            f"{s.SUPABASE_URL}/rest/v1/recognition_logs",
                            json={"resultado_real": resultado_real},
                            headers={
                                "apikey": s.SUPABASE_SERVICE_ROLE_KEY,
                                "Authorization": f"Bearer {s.SUPABASE_SERVICE_ROLE_KEY}",
                                "Content-Type": "application/json",
                                "Prefer": "return=minimal",
                            },
                            params={"id": f"eq.{log_id}"},
                            timeout=15,
                        )
                except Exception:
                    pass

                try:
                    embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                    train_features = _build_features(match, face_data)
                    train_features["embedding"] = embedding_list
                    train_features["fuente"] = "reconocimiento"
                    audit_service.log_training_record(
                        features=train_features,
                        resultado_real=resultado_real,
                    )
                    try:
                        stats = supabase_admin.table("ml_training_records").select(
                            "id", count="exact"
                        ).execute()
                        total = stats.count or 0
                        positive_r = supabase_admin.table(
                            "ml_training_records"
                        ).select("id", count="exact").eq("resultado_real", True).execute()
                        negative_r = supabase_admin.table(
                            "ml_training_records"
                        ).select("id", count="exact").eq("resultado_real", False).execute()
                        if positive_r.count >= settings.MIN_TRAIN_PER_CLASS and negative_r.count >= settings.MIN_TRAIN_PER_CLASS:
                            from app.ml.trainer import train_model
                            train_model()
                            print(f"[reconocimiento] ML reentrenado: {total} registros")
                    except Exception as e:
                        print(f"[reconocimiento] Error reentrenamiento: {e}")
                except Exception:
                    pass
        except Exception as e:
            print(f"[reconocimiento] ERROR audit: {e}")
            log_id = None

        print(f"[reconocimiento] === FIN OK ===")
        return {
            "success": True,
            "es_humano": True,
            "coincide": coincide,
            "log_id": log_id,
            "resultado_real": resultado_real,
            "clasificacion": clasificacion,
            "resultado": {
                "coincide": coincide,
                "persona_id": str(persona["id"]) if persona else None,
                "nombre": persona.get("nombre") if persona else None,
                "email": persona.get("email") if persona else None,
                "similitud": float(matches[0]["similitud"]) if matches else 0.0,
                "distancia": float(matches[0]["distancia"]) if matches else 1.0,
                "umbral": settings.UMBRAL_SIMILITUD,
                "probabilidad_calibrada": prob,
                "resultado_real": resultado_real,
                "clasificacion": clasificacion,
                "calidad_imagen": round(face_data["quality"], 4),
                "iluminacion": round(face_data["illumination"], 4),
            },
            "top_matches": [
                {
                    "persona_id": str(m.get("persona_id")),
                    "nombre": m.get("nombre"),
                    "similitud": round(float(m.get("similitud", 0)), 4),
                }
                for m in matches[:5]
            ],
        }

    except HTTPException:
        raise
    except ValueError as e:
        # El DL no detectó un rostro humano (objeto, animal, dibujo, etc.)
        print(f"[reconocimiento] ValueError (no es humano): {e}")
        return {
            "success": True,
            "es_humano": False,
            "coincide": False,
            "clasificacion": "no_humano",
            "resultado": None,
            "detail": str(e),
        }
    except Exception as e:
        print(f"[reconocimiento] ERROR GENERAL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el reconocimiento: {str(e)[:200]}")


@router.get("/historial")
async def historial(user: dict = Depends(get_current_user)):
    try:
        from app.services.audit_service import audit_service
        logs = audit_service.get_recent_logs(limit=100)
        return {"success": True, "historial": logs or []}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"success": True, "historial": [], "warning": f"Error: {str(e)[:100]}"}


@router.delete("/historial")
async def borrar_historial(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        supabase_admin.table("recognition_logs").delete().neq("id", "").execute()
        return {"success": True, "message": "Historial eliminado"}
    except Exception as e:
        logger.error(f"Error deleting history: {e}")
        raise HTTPException(status_code=500, detail=f"Error al borrar historial: {str(e)[:200]}")


@router.get("/historial/csv")
async def historial_csv(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        result = (
            supabase_admin.table("recognition_logs")
            .select("id, persona_id, similitud, distancia, umbral, coincide, probabilidad_calibrada, resultado_real, created_at, personas(nombre, email)")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        rows = result.data or []
        lines = ["Fecha,Persona,Email,Similitud,Distancia,Umbral,Coincide,Probabilidad,Estado"]
        for r in rows:
            persona = r.get("personas") or {}
            lines.append(
                f'{r.get("created_at","")},{persona.get("nombre","Desconocido")},{persona.get("email","")},'
                f'{r.get("similitud",0)},{r.get("distancia",0)},{r.get("umbral",0)},'
                f'{"Si" if r.get("coincide") else "No"},'
                f'{r.get("probabilidad_calibrada","") if r.get("probabilidad_calibrada") is not None else ""},'
                f'{"Correcto" if r.get("resultado_real") is True else "Incorrecto" if r.get("resultado_real") is False else "Sin confirmar"}'
            )
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("\n".join(lines), media_type="text/csv",
                                headers={"Content-Disposition": "attachment; filename=historial.csv"})
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando CSV: {str(e)[:200]}")


@router.patch("/historial/{log_id}/confirmar")
async def confirmar_resultado(log_id: str, data: dict, user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        clasificacion = data.get("clasificacion", "")
        resultado_real = data.get("resultado_real")

        if clasificacion:
            classification_map = {
                "humano_real": True,
                "humano_semi_real": True,
                "no_real_detectado": False,
                "no_real_rechazado": False,
                "humano": True,
                "no_real": False,
            }
            if clasificacion not in classification_map:
                raise HTTPException(status_code=400, detail=f"Clasificacion invalida: {clasificacion}")
            resultado_real = classification_map[clasificacion]
        elif resultado_real is None:
            raise HTTPException(status_code=400, detail="clasificacion o resultado_real es requerido")

        log_result = supabase_admin.table("recognition_logs").select("*").eq("id", log_id).execute()
        if not log_result.data:
            raise HTTPException(status_code=404, detail="Registro no encontrado")

        log_entry = log_result.data[0]

        import httpx
        s = get_settings()
        rest_url = f"{s.SUPABASE_URL}/rest/v1/recognition_logs"
        rest_headers = {
            "apikey": s.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {s.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        update_payload = {"resultado_real": resultado_real}
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                rest_url,
                json=update_payload,
                headers=rest_headers,
                params={"id": f"eq.{log_id}"},
                timeout=15,
            )
        if resp.status_code not in (200, 204):
            logger.error(f"PostgREST confirm error: {resp.status_code} {resp.text[:300]}")
            raise HTTPException(status_code=500, detail=f"Error guardando: {resp.text[:200]}")

        from app.services.audit_service import audit_service
        try:
            log_features = {
                "similitud": log_entry["similitud"],
                "calidad_imagen": log_entry.get("calidad_imagen") or 0.5,
                "iluminacion": log_entry.get("iluminacion") or 0.5,
                "distancia": log_entry["distancia"],
            }
            for k in ML_FEATURE_KEYS:
                val = log_entry.get(k)
                if val is not None:
                    log_features[k] = val
            emb_val = log_entry.get("embedding")
            if emb_val is not None:
                log_features["embedding"] = emb_val
            audit_service.log_training_record(
                features=log_features,
                resultado_real=resultado_real,
            )
        except Exception:
            pass

        retrained = False
        try:
            import httpx as _httpx
            _s = get_settings()
            _h = {"apikey": _s.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}"}
            _r = _httpx.get(f"{_s.SUPABASE_URL}/rest/v1/ml_training_records",
                           params={"select": "resultado_real"}, headers=_h, timeout=30)
            if _r.status_code == 200:
                _rows = _r.json() or []
                pos_count = sum(1 for row in _rows if row.get("resultado_real") in (True, "true", "True", 1))
                neg_count = sum(1 for row in _rows if row.get("resultado_real") in (False, "false", "False", 0))
            else:
                pos_count = 0
                neg_count = 0
            if pos_count >= settings.MIN_TRAIN_PER_CLASS and neg_count >= settings.MIN_TRAIN_PER_CLASS:
                from app.ml.trainer import train_model
                train_model()
                retrained = True
                logger.info(f"Auto-retrained after confirm: {pos_count} pos, {neg_count} neg")
        except Exception as e:
            logger.warning(f"Auto-retrain after confirm failed: {e}")

        return {"success": True, "message": "Clasificacion guardada", "clasificacion": clasificacion, "retrained": retrained}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming result: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.get("/personas-count")
async def personas_count(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        result = supabase_admin.table("personas").select("id", count="exact").execute()
        return {"success": True, "total": result.count or 0}
    except Exception as e:
        logger.error(f"Error counting personas: {e}")
        return {"success": True, "total": 0}


@router.get("/audit-log")
async def audit_log(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        result = (
            supabase_admin.table("recognition_logs")
            .select("id, persona_id, similitud, distancia, umbral, coincide, probabilidad_calibrada, resultado_real, created_at, personas(nombre)")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return {"success": True, "logs": result.data or []}
    except Exception as e:
        logger.error(f"Error fetching audit log: {e}")
        return {"success": True, "logs": []}


@router.post("/auto-confirmar")
async def auto_confirmar_pendientes(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        # No auto-clasificar si NINGUN modelo esta entrenado (daria etiquetas al azar).
        from app.services.probability_service import probability_service
        if probability_service.model is None and probability_service.emb_model is None:
            return {
                "success": False,
                "confirmed": 0,
                "message": "El modelo ML aun no esta entrenado. Confirma manualmente o entrena primero (Entrenamiento ML).",
            }

        result = supabase_admin.table("recognition_logs").select("*").is_("resultado_real", "null").execute()
        pending = result.data or []
        if not pending:
            return {"success": True, "message": "No hay registros pendientes", "confirmed": 0}

        from app.services.audit_service import audit_service

        classification_map = {
            "humano_real": {"resultado_real": True},
            "no_real": {"resultado_real": False},
        }

        from app.services.probability_service import probability_service

        confirmed = 0
        for log in pending:
            coincide = log.get("coincide", False)
            persona_id = log.get("persona_id")

            prob = None
            umbral_log = probability_service.umbral_decision
            # Si el log ya trae la probabilidad calculada (flujo por embedding), la
            # reutilizamos; si no, predecimos con el modelo de 4 variables.
            prob_guardada = log.get("probabilidad_calibrada")
            if prob_guardada is not None:
                prob = float(prob_guardada)
                if probability_service.emb_model is not None:
                    umbral_log = probability_service.umbral_embedding
            else:
                try:
                    features = _build_features_from_log(log)
                    prob = probability_service.predecir(features)
                except Exception:
                    pass

            if prob is not None:
                clasificacion = "humano_real" if prob >= umbral_log else "no_real"
            elif coincide and persona_id:
                clasificacion = "humano_real"
            else:
                clasificacion = "no_real"

            mapping = classification_map[clasificacion]
            try:
                import httpx
                s = get_settings()
                async with httpx.AsyncClient() as cl:
                    await cl.patch(
                        f"{s.SUPABASE_URL}/rest/v1/recognition_logs",
                        json={"resultado_real": mapping["resultado_real"]},
                        headers={
                            "apikey": s.SUPABASE_SERVICE_ROLE_KEY,
                            "Authorization": f"Bearer {s.SUPABASE_SERVICE_ROLE_KEY}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        },
                        params={"id": f"eq.{log['id']}"},
                        timeout=15,
                    )
            except Exception:
                pass

            try:
                if prob is not None:
                    auto_features = _build_features_from_log(log)
                    emb_val = log.get("embedding")
                    if emb_val is not None:
                        auto_features["embedding"] = emb_val
                    audit_service.log_training_record(
                        features=auto_features,
                        resultado_real=mapping["resultado_real"],
                    )
            except Exception:
                pass
            confirmed += 1

        retrained = False
        try:
            import httpx as _httpx
            _s = get_settings()
            _h = {"apikey": _s.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}"}
            _r = _httpx.get(f"{_s.SUPABASE_URL}/rest/v1/ml_training_records",
                           params={"select": "resultado_real"}, headers=_h, timeout=30)
            if _r.status_code == 200:
                _rows = _r.json() or []
                pos_count = sum(1 for row in _rows if row.get("resultado_real") in (True, "true", "True", 1))
                neg_count = sum(1 for row in _rows if row.get("resultado_real") in (False, "false", "False", 0))
            else:
                pos_count = 0
                neg_count = 0
            if pos_count >= settings.MIN_TRAIN_PER_CLASS and neg_count >= settings.MIN_TRAIN_PER_CLASS:
                from app.ml.trainer import train_model
                train_model()
                retrained = True
        except Exception as e:
            logger.warning(f"Auto-retrain after batch confirm: {e}")

        return {"success": True, "message": f"{confirmed} registros confirmados automaticamente", "confirmed": confirmed, "retrained": retrained}
    except Exception as e:
        logger.error(f"Auto-confirm error: {e}")
        raise HTTPException(status_code=500, detail=f"Error auto-confirmando: {str(e)[:200]}")
