from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.supabase_client import supabase_admin
from app.core.logging_config import logger
from app.core.security import create_access_token
from app.api.deps import get_current_admin
import hashlib
import secrets

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split(':')
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    except Exception:
        return False


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "operador"


ALLOWED_ROLES = {"admin", "operador", "analista"}


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Rol invalido. Roles permitidos: {', '.join(ALLOWED_ROLES)}")

    existing = supabase_admin.table("users").select("id").eq("email", req.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    password_hash = _hash_password(req.password)

    try:
        from app.core.config import get_settings
        settings = get_settings()
        import httpx

        url = f"{settings.SUPABASE_URL}/rest/v1/users"
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        payload = {
            "name": req.name,
            "email": req.email,
            "password_hash": password_hash,
            "role": req.role,
            "active": True,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code not in (200, 201):
            logger.error(f"Supabase REST insert error: {resp.status_code} {resp.text[:200]}")
            raise HTTPException(status_code=500, detail=f"Error al registrar: {resp.text[:200]}")
        user = resp.json()[0] if resp.json() else {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al registrar: {str(e)[:200]}")

    logger.info(f"User registered: {req.email}")

    return {
        "success": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        },
    }


@router.post("/login")
async def login(req: LoginRequest):
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    result = supabase_admin.table("users").select("*").eq("email", req.email).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    user = result.data[0]
    if not user.get("active", False):
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    if not _verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    logger.info(f"User logged in: {req.email}")

    token = create_access_token({"sub": user["id"], "role": user["role"], "name": user["name"], "email": user["email"]})

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.get("/users")
async def list_users(user: dict = Depends(get_current_admin)):
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    try:
        from app.core.config import get_settings
        settings = get_settings()
        import httpx

        url = f"{settings.SUPABASE_URL}/rest/v1/users?select=id,name,email,role,active,created_at&order=created_at.desc"
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Supabase REST list error: {resp.status_code} {resp.text[:200]}")
            raise HTTPException(status_code=500, detail=f"Error listando usuarios: {resp.text[:200]}")
        users = resp.json()
        return {"success": True, "users": users or []}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando usuarios: {str(e)[:200]}")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, user: dict = Depends(get_current_admin)):
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    try:
        from app.core.config import get_settings
        settings = get_settings()
        import httpx

        existing = supabase_admin.table("users").select("id, email").eq("id", user_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if existing.data[0].get("email") == "admin@badicorp.com":
            raise HTTPException(status_code=400, detail="No se puede eliminar al administrador principal")

        rest_url = f"{settings.SUPABASE_URL}/rest/v1/users"
        rest_headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                rest_url,
                headers=rest_headers,
                params={"id": f"eq.{user_id}"},
                timeout=15,
            )
        if resp.status_code not in (200, 204):
            logger.error(f"PostgREST delete error: {resp.status_code} {resp.text[:200]}")
            raise HTTPException(status_code=500, detail=f"Error al eliminar: {resp.text[:200]}")
        return {"success": True, "message": "Usuario eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)[:200]}")


class ChangeRoleRequest(BaseModel):
    role: str


@router.post("/fix-role-constraint")
async def fix_role_constraint(user: dict = Depends(get_current_admin)):
    """Crea una funcion SQL exec_sql y arregla el constraint de roles. Ejecutar una vez."""
    try:
        from app.core.config import get_settings
        settings = get_settings()
        import httpx

        create_fn = """
CREATE OR REPLACE FUNCTION exec_sql(query TEXT)
RETURNS TEXT AS $$
BEGIN
  EXECUTE query;
  RETURN 'OK';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""
        fix_constraint = """
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT conname FROM pg_constraint WHERE conrelid = 'users'::regclass AND contype = 'c' LOOP
    EXECUTE 'ALTER TABLE users DROP CONSTRAINT IF EXISTS ' || quote_ident(r.conname);
  END LOOP;
END $$;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'operador', 'analista'));
"""
        url = f"{settings.SUPABASE_URL}/rest/v1/rpc/exec_sql"
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

        sql_url = f"{settings.SUPABASE_URL}/sql"
        async with httpx.AsyncClient() as client:
            resp = await client.post(sql_url, json={"query": create_fn + fix_constraint}, headers=headers, timeout=30)
            if resp.status_code not in (200, 201, 204):
                return {"success": False, "status": resp.status_code, "body": resp.text[:500], "hint": "Ejecuta el SQL manualmente en Supabase SQL Editor"}
        return {"success": True, "message": "Constraint arreglado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:200])


@router.patch("/users/{user_id}/role")
async def change_role(user_id: str, req: ChangeRoleRequest, user: dict = Depends(get_current_admin)):
    if supabase_admin is None:
        raise HTTPException(status_code=503, detail="Supabase no conectado")

    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Rol invalido. Roles permitidos: {', '.join(ALLOWED_ROLES)}")

    try:
        from app.core.config import get_settings
        settings = get_settings()
        import httpx

        existing = supabase_admin.table("users").select("id, email").eq("id", user_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        rest_url = f"{settings.SUPABASE_URL}/rest/v1/users"
        rest_headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                rest_url,
                json={"role": req.role},
                headers=rest_headers,
                params={"id": f"eq.{user_id}"},
                timeout=15,
            )
        if resp.status_code not in (200, 204):
            logger.error(f"PostgREST update error: {resp.status_code} {resp.text[:200]}")
            raise HTTPException(status_code=500, detail=f"Error en base de datos: {resp.text[:200]}")
        logger.info(f"User {user_id} role changed to {req.role}")
        return {"success": True, "message": f"Rol cambiado a {req.role}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change role error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cambiar rol: {str(e)[:200]}")
