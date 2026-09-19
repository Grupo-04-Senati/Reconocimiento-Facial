try:
    from supabase import create_client, Client
    _SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"[supabase_client] WARNING: supabase not available: {e}")
    Client = None
    _SUPABASE_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()

supabase_admin = None
supabase_client = None


def _init_supabase():
    global supabase_admin, supabase_client
    if not _SUPABASE_AVAILABLE:
        print("[supabase_client] Skipping init - supabase not installed")
        return
    try:
        supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        print(f"[supabase_client] Connected: {settings.SUPABASE_URL}")
    except Exception as e:
        print(f"[supabase_client] Connection failed: {e}")
        print("[supabase_client] Running offline - some features unavailable")


try:
    _init_supabase()
except Exception as e:
    print(f"[supabase_client] Init error: {e}")
