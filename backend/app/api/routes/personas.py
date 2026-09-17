from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.supabase_client import supabase_admin
from app.services.face_service import face_service
from app.services.storage_service import storage_service
from app.services.embedding_service import embedding_service
from app.core.logging_config import logger

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.post("")
async def registrar_persona(
    nombre: str = Form(...),
    email: str = Form(...),
    imagen: UploadFile = File(...),
):
    try:
        existing = (
            supabase_admin.table("personas")
            .select("id")
            .eq("email", email)
            .execute()
        )
        if existing.data:
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        persona = supabase_admin.table("personas").insert(
            {"nombre": nombre, "email": email, "activo": True}
        ).execute()

        persona_id = persona.data[0]["id"]

        image_bytes = await imagen.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no debe exceder 5MB")

        embedding = face_service.get_embedding(image_bytes)

        image_url = storage_service.upload_face_image(persona_id, image_bytes)

        embedding_service.save_embedding(
            persona_id=persona_id,
            embedding=embedding,
            modelo="arcface",
            image_url=image_url,
        )

        logger.info(f"Persona registered: {nombre} ({email})")

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
        logger.error(f"Error registering persona: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("")
async def listar_personas():
    try:
        result = supabase_admin.table("personas").select("*").execute()
        return {"success": True, "personas": result.data}
    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{persona_id}")
async def obtener_persona(persona_id: str):
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
        logger.error(f"Error getting persona: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{persona_id}")
async def eliminar_persona(persona_id: str):
    try:
        result = (
            supabase_admin.table("personas")
            .select("id")
            .eq("id", persona_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Persona no encontrada")

        storage_service.delete_face_image(persona_id)
        supabase_admin.table("personas").delete().eq("id", persona_id).execute()

        logger.info(f"Persona deleted: {persona_id}")
        return {"success": True, "message": "Persona eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting persona: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
