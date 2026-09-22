"""
Cliente Supabase con inicializacion LAZY.
NO conecta al importar. Conecta solo al primer uso.
Incluye helpers POSTgREST que funcionan directo via httpx.
"""
from __future__ import annotations
import httpx

_SUPABASE_AVAILABLE = False
_supabase_admin = None
_supabase_client = None
_initialized = False
_settings = None


def _ensure_imported():
    global _SUPABASE_AVAILABLE
    try:
        import supabase
        _SUPABASE_AVAILABLE = True
    except ImportError as e:
        print(f"[supabase_client] supabase not available: {e}")
        _SUPABASE_AVAILABLE = False


def _get_settings():
    global _settings
    if _settings is None:
        from app.core.config import get_settings
        _settings = get_settings()
    return _settings


def _rest_url(table: str) -> str:
    s = _get_settings()
    return f"{s.SUPABASE_URL}/rest/v1/{table}"


def _rest_headers(prefer: str = "return=minimal") -> dict:
    s = _get_settings()
    return {
        "apikey": s.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {s.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


async def sb_update(table: str, data: dict, filters: dict) -> int:
    """Update rows via PostgREST. Returns number of rows affected."""
    params = {k: f"eq.{v}" for k, v in filters.items()}
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            _rest_url(table),
            json=data,
            headers=_rest_headers(),
            params=params,
            timeout=15,
        )
    if resp.status_code not in (200, 204):
        print(f"[sb_update] ERROR {table}: {resp.status_code} {resp.text[:200]}")
    return 0


async def sb_delete(table: str, filters: dict) -> int:
    """Delete rows via PostgREST."""
    params = {k: f"eq.{v}" for k, v in filters.items()}
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            _rest_url(table),
            headers=_rest_headers(),
            params=params,
            timeout=15,
        )
    if resp.status_code not in (200, 204):
        print(f"[sb_delete] ERROR {table}: {resp.status_code} {resp.text[:200]}")
    return 0


async def sb_delete_all(table: str) -> int:
    """Delete ALL rows from a table. Uses neq filter (PostgREST requires a filter)."""
    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            _rest_url(table),
            headers=_rest_headers(),
            params={"id": "neq.00000000-0000-0000-0000-000000000000"},
            timeout=30,
        )
    if resp.status_code not in (200, 204):
        print(f"[sb_delete_all] ERROR {table}: {resp.status_code} {resp.text[:200]}")
    return 0


async def sb_select_count(table: str, filters: dict = None) -> int:
    """Count rows via PostgREST."""
    params = {"select": "id", "Head": "true"}
    if filters:
        for k, v in filters.items():
            params[k] = f"eq.{v}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _rest_url(table),
            headers=_rest_headers(prefer="count=exact"),
            params=params,
            timeout=15,
        )
    count_header = resp.headers.get("content-range", "")
    if "/" in count_header:
        try:
            return int(count_header.split("/")[1])
        except (ValueError, IndexError):
            pass
    return 0


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
