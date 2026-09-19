import uuid
from app.core.supabase_client import supabase_admin
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()


class StorageService:
    def upload_face_image(self, persona_id: str, image_bytes: bytes) -> str:
        filename = f"{persona_id}/{uuid.uuid4().hex}.jpg"

        result = supabase_admin.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
            path=filename,
            file=image_bytes,
            file_options={"content-type": "image/jpeg"},
        )

        public_url = supabase_admin.storage.from_(
            settings.SUPABASE_STORAGE_BUCKET
        ).get_public_url(filename)

        logger.info(f"Image uploaded: {filename}")
        return public_url

    def delete_face_image(self, persona_id: str) -> bool:
        try:
            files = supabase_admin.storage.from_(
                settings.SUPABASE_STORAGE_BUCKET
            ).list(persona_id)

            if files:
                paths = [f"{persona_id}/{f['name']}" for f in files]
                supabase_admin.storage.from_(
                    settings.SUPABASE_STORAGE_BUCKET
                ).remove(paths)
                logger.info(f"Deleted {len(paths)} images for persona {persona_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting images: {e}")
            return False


storage_service = StorageService()
