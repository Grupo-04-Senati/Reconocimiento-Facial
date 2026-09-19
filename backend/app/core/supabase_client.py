from supabase import create_client, Client
from app.core.config import get_settings
from app.core.logging_config import logger

settings = get_settings()

supabase_admin: Client = None
supabase_client: Client = None


def _init_supabase():
    global supabase_admin, supabase_client
    try:
        supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        logger.info(f"Supabase connected: {settings.SUPABASE_URL}")
    except Exception as e:
        logger.warning(f"Supabase connection failed: {e}")
        logger.warning("Running in offline mode - some features unavailable")


try:
    _init_supabase()
except Exception:
    pass
