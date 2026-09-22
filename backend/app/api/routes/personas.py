from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/personas", tags=["personas"])
settings = get_settings()


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase no conectado. Verifica la conexion a internet y las credenciales.",
        )


@router.get("")
async def listar_personas(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        result = supabase_admin.table("personas").select("*").order("created_at", desc=True).execute()
        return {"success": True, "personas": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar personas: {str(e)[:200]}")


@router.get("/con-embedding")
async def listar_personas_con_embedding(user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        emb_result = supabase_admin.table("face_embeddings").select("persona_id").execute()
        persona_ids = list(set(e["persona_id"] for e in (emb_result.data or []) if e.get("persona_id")))
        if not persona_ids:
            return {"success": True, "personas": []}
        result = supabase_admin.table("personas").select("*").in_("id", persona_ids).order("created_at", desc=True).execute()
        return {"success": True, "personas": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar personas con embedding: {str(e)[:200]}")


@router.get("/{persona_id}")
async def obtener_persona(persona_id: str, user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        result = supabase_admin.table("personas").select("*").eq("id", persona_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return {"success": True, "persona": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.post("")
async def registrar_persona(
    nombre: str = Form(...),
    email: str = Form(...),
    imagen: UploadFile = File(...),
    tipo: str = Form("real"),
    user: dict = Depends(get_current_user),
):
    _check_supabase()
    persona_id = None
    try:
        print(f"[personas] POST /api/personas: nombre={nombre}, email={email}")

        from app.services.face_service import face_service

        print(f"[personas] Modelo cargado: {face_service._initialized}")

        if not face_service._initialized:
            raise HTTPException(
                status_code=503,
                detail="Modelo IA no disponible. Intenta de nuevo en unos segundos.",
            )

        existing = (
            supabase_admin.table("personas")
            .select("id")
            .eq("email", email)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=400, detail="El email ya esta registrado")

        print(f"[personas] Insertando persona en Supabase...")
        tipo_val = "ia" if str(tipo).lower() == "ia" else "real"
        payload = {"nombre": nombre, "email": email, "activo": True, "tipo": tipo_val}
        try:
            persona = supabase_admin.table("personas").insert(payload).execute()
        except Exception as e:
            # Fallback si la columna 'tipo' aun no existe (migracion 012 no aplicada)
            print(f"[personas] insert con tipo fallo ({e}); reintento sin tipo")
            payload.pop("tipo", None)
            persona = supabase_admin.table("personas").insert(payload).execute()

        persona_id = persona.data[0]["id"]
        print(f"[personas] Persona creada: {persona_id}")

        image_bytes = await imagen.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no debe exceder 5MB")

        print(f"[personas] Obteniendo embedding facial...")
        # Con calidad/iluminacion reales para que el dato de entrenamiento sea
        # consistente (antes se usaba 0.5 por defecto y confundia al modelo).
        face_data = face_service.get_embedding_with_quality(image_bytes)
        embedding = face_data["embedding"]
        print(f"[personas] Embedding: type={type(embedding)}, shape={embedding.shape}")

        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        print(f"[personas] Embedding list: len={len(embedding_list)}")

        print(f"[personas] Insertando en face_embeddings...")
        embedding_result = supabase_admin.table("face_embeddings").insert(
            {
                "persona_id": str(persona_id),
                "embedding": embedding_list,
                "modelo": "buffalo_s",
            }
        ).execute()
        print(f"[personas] Embedding guardado OK: {embedding_result.data}")

        print(f"[personas] Registro exitoso: {nombre} ({email})")

        try:
            from app.services.audit_service import audit_service
            log_result = audit_service.log_recognition(
                persona_id=str(persona_id),
                similitud=1.0,
                distancia=0.0,
                umbral=settings.UMBRAL_SIMILITUD,
                coincide=True,
                probabilidad_calibrada=1.0,
                calidad_imagen=face_data["quality"],
                iluminacion=face_data["illumination"],
            )
            print(f"[personas] Log de reconocimiento auto-creado: {log_result.get('id')}")

            # Auto-registro ML: cada persona registrada = dato "humano_real"
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            audit_service.log_training_record(
                features={
                    "similitud": 1.0,
                    "distancia": 0.0,
                    "calidad_imagen": face_data["quality"],
                    "iluminacion": face_data["illumination"],
                    "textura": face_data.get("textura"),
                    "frecuencia_baja": face_data.get("frecuencia_baja"),
                    "frecuencia_alta": face_data.get("frecuencia_alta"),
                    "ruido": face_data.get("ruido"),
                    "contraste_textura": face_data.get("contraste_textura"),
                    "asimetria": face_data.get("asimetria"),
                    "brillo_variacion": face_data.get("brillo_variacion"),
                    "edge_consistency": face_data.get("edge_consistency"),
                    "fft_varianza": face_data.get("fft_varianza"),
                    "freq_edge_mean": face_data.get("freq_edge_mean"),
                    "freq_edge_var": face_data.get("freq_edge_var"),
                    "lbp_mean": face_data.get("lbp_mean"),
                    "lbp_var": face_data.get("lbp_var"),
                    "lbp_contraste": face_data.get("lbp_contraste"),
                    "entropy": face_data.get("entropy"),
                    "skin_smoothness": face_data.get("skin_smoothness"),
                    "embedding": embedding_list,
                    "fuente": "registro",
                },
                resultado_real=True,
            )
            print(f"[personas] ML record auto-creado para {nombre}")
        except Exception as e:
            print(f"[personas] WARNING: no se pudo crear log/ML record: {e}")

        return {
            "success": True,
            "persona_id": persona_id,
            "message": f"Persona '{nombre}' registrada exitosamente",
        }

    except HTTPException:
        raise
    except ValueError as e:
        print(f"[personas] ValueError: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[personas] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        if persona_id:
            print(f"[personas] Rollback: eliminando persona {persona_id}...")
            try:
                supabase_admin.table("personas").delete().eq("id", persona_id).execute()
                print(f"[personas] Rollback OK")
            except Exception as rollback_error:
                print(f"[personas] Rollback failed: {rollback_error}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)[:200]}")


@router.post("/{persona_id}/rostro")
async def agregar_rostro(persona_id: str, imagen: UploadFile = File(...), user: dict = Depends(get_current_user)):
    _check_supabase()
    try:
        print(f"[personas] POST /api/personas/{persona_id}/rostro")

        existing = supabase_admin.table("personas").select("id").eq("id", persona_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        from app.services.face_service import face_service
        if not face_service._initialized:
            raise HTTPException(status_code=503, detail="Modelo IA no disponible")

        image_bytes = await imagen.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no debe exceder 5MB")

        embedding = face_service.get_embedding(image_bytes)
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)

        result = supabase_admin.table("face_embeddings").insert(
            {
                "persona_id": str(persona_id),
                "embedding": embedding_list,
                "modelo": "buffalo_s",
            }
        ).execute()

        print(f"[personas] Embedding guardado para persona {persona_id}")
        return {
            "success": True,
            "message": "Rostro agregado exitosamente",
            "embedding_id": result.data[0]["id"] if result.data else None,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[personas] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)[:200]}")
