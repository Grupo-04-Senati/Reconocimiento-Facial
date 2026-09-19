"""
Cliente Supabase con inicializacion LAZY.
NO conecta al importar. Conecta solo al primer uso.
"""
from __future__ import annotations

_SUPABASE_AVAILABLE = False
_supabase_admin = None
_supabase_client = None
_initialized = False


def _ensure_imported():
    global _SUPABASE_AVAILABLE
    try:
        import supabase
        _SUPABASE_AVAILABLE = True
    except ImportError as e:
        print(f"[supabase_client] supabase not available: {e}")
        _SUPABASE_AVAILABLE = False


def _init():
    global _supabase_admin, _supabase_client, _initialized
    if _initialized:
        return
    _ensure_imported()
    if not _SUPABASE_AVAILABLE:
        print("[supabase_client] Skipping init - supabase not installed")
        _initialized = True
        return
    try:
        from app.core.config import get_settings
        settings = get_settings()
        from supabase import create_client
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        print(f"[supabase_client] Connected: {settings.SUPABASE_URL}")
    except Exception as e:
        print(f"[supabase_client] Connection failed: {e}")
    _initialized = True


def get_supabase_admin():
    _init()
    return _supabase_admin


def get_supabase_client():
    _init()
    return _supabase_client


# Para compatibilidad con codigo existente que usa `from ... import supabase_admin`
# Esto crea un proxy lazy que no conecta hasta que se accede a un atributo
class _LazySupabase:
    def __init__(self, getter):
        self._getter = getter
        self._real = None

    def _get_real(self):
        if self._real is None:
            self._real = self._getter()
        return self._real

    def __getattr__(self, name):
        return getattr(self._get_real(), name)

    def __bool__(self):
        return self._get_real() is not None


supabase_admin = _LazySupabase(get_supabase_admin)
supabase_client = _LazySupabase(get_supabase_client)
