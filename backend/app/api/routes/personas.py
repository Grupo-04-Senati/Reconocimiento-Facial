from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger

router = APIRouter(prefix="/api/personas", tags=["personas"])


def _check_supabase():
    if supabase_admin is None:
        raise HTTPException(
            status_code=503,
            detail="Supabase no conectado. Verifica la conexion a internet y las credenciales.",
        )


@router.post("")
async def registrar_persona(
    nombre: str = Form(...),
    email: str = Form(...),
    imagen: UploadFile = File(...),
):
    _check_supabase()
    try:
        print(f"[personas] POST /api/personas: nombre={nombre}, email={email}")

        from app.services.face_service import face_service
        from app.ml.vector_store import vector_store

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
        persona = supabase_admin.table("personas").insert(
            {"nombre": nombre, "email": email, "activo": True}
        ).execute()

        persona_id = persona.data[0]["id"]
        print(f"[personas] Persona creada: {persona_id}")

        image_bytes = await imagen.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no debe exceder 5MB")

        print(f"[personas] Obteniendo embedding facial...")
        try:
            embedding = face_service.get_embedding(image_bytes)
            print(f"[personas] Embedding obtenido: shape={embedding.shape}")
        except Exception as e:
            print(f"[personas] ERROR get_embedding: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

        print(f"[personas] Guardando embedding en pgvector...")
        try:
            vector_store.save_embedding(
                persona_id=persona_id,
                embedding=embedding,
                modelo="buffalo_s",
            )
            print(f"[personas] Embedding guardado OK")
        except Exception as e:
            print(f"[personas] ERROR save_embedding: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

        print(f"[personas] Registro exitoso: {nombre} ({email})")

        return {
            "success": True,
            "persona_id": persona_id,
            "message": f"Persona '{nombre}' registrada exitosamente",
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


@router.post("/{persona_id}/rostro")
async def guardar_rostro(persona_id: str, imagen: UploadFile = File(...)):
    _check_supabase()
    try:
        from app.services.face_service import face_service
        from app.ml.vector_store import vector_store

        existing = (
            supabase_admin.table("personas")
            .select("id")
            .eq("id", persona_id)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        image_bytes = await imagen.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no debe exceder 5MB")

        embedding = face_service.get_embedding(image_bytes)

        vector_store.save_embedding(
            persona_id=persona_id,
            embedding=embedding,
            modelo="buffalo_s",
        )

        return {
            "success": True,
            "message": "Embedding facial guardado exitosamente",
            "embedding_model": "arcface",
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"[personas] ERROR guardar_rostro: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)[:200]}")


@router.get("")
async def listar_personas():
    _check_supabase()
    try:
        result = supabase_admin.table("personas").select("*").execute()
        return {"success": True, "personas": result.data}
    except Exception as e:
        print(f"[personas] ERROR listar: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{persona_id}")
async def obtener_persona(persona_id: str):
    _check_supabase()
    try:
        result = (
            supabase_admin.table("personas")
            .select("*")
            .eq("id", persona_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return {"success": True, "persona": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[personas] ERROR obtener: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{persona_id}")
async def eliminar_persona(persona_id: str):
    _check_supabase()
    try:
        result = (
            supabase_admin.table("personas")
            .select("id")
            .eq("id", persona_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        supabase_admin.table("personas").delete().eq("id", persona_id).execute()

        return {"success": True, "message": "Persona eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[personas] ERROR eliminar: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
