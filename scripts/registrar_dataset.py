# -*- coding: utf-8 -*-
"""
Registra en la BASE DE DATOS (via el backend) las fotos de personas reales
que estan en frontend/public/imagenes/realhumanos/.

Cada foto se convierte en un embedding facial (Deep Learning) y se guarda en
Supabase como una persona registrada. Asi el sistema podra reconocerlas, en
vez de tenerlas como imagenes estaticas.

Las de 'falsoshumanos/' NO se registran (no son personas): sirven para PROBAR
el resultado "No es humano" subiendolas en la pestana Reconocimiento.

--------------------------------------------------------------------------
COMO USARLO (lo corres tu, con tus credenciales de admin):

  1) Instala requests (una vez):
       pip install requests

  2) Define tus credenciales de admin en la terminal:
       PowerShell (Windows):
         $env:ADMIN_EMAIL   = "tu-correo@ejemplo.com"
         $env:ADMIN_PASSWORD= "tu-contrasena"
       (opcional, si tu backend no es el de Railway por defecto)
         $env:API_URL = "https://tu-backend"

  3) Ejecuta desde la raiz del proyecto:
       python scripts/registrar_dataset.py
--------------------------------------------------------------------------
"""
import os
import sys
import glob

try:
    import requests
except ImportError:
    print("Falta la libreria 'requests'. Instalala con:  pip install requests")
    sys.exit(1)

API_URL = os.environ.get(
    "API_URL", "https://reconocimiento-facial-production-1b3a.up.railway.app"
).rstrip("/")
EMAIL = os.environ.get("ADMIN_EMAIL", "")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_DIR = os.path.join(BASE, "frontend", "public", "imagenes", "realhumanos")

VALID_EXT = (".jpg", ".jpeg", ".png", ".webp", ".avif")


def login() -> str:
    if not EMAIL or not PASSWORD:
        print("ERROR: define ADMIN_EMAIL y ADMIN_PASSWORD como variables de entorno.")
        print("Ejemplo PowerShell:")
        print('  $env:ADMIN_EMAIL="tu-correo@ejemplo.com"')
        print('  $env:ADMIN_PASSWORD="tu-contrasena"')
        sys.exit(1)
    print(f"Iniciando sesion en {API_URL} ...")
    r = requests.post(
        f"{API_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"ERROR de login ({r.status_code}): {r.text[:200]}")
        sys.exit(1)
    data = r.json()
    token = data.get("token")
    if not token:
        print("ERROR: el login no devolvio token. Respuesta:", data)
        sys.exit(1)
    print("Login OK.")
    return token


def registrar(token: str, path: str, nombre: str, email: str):
    with open(path, "rb") as f:
        files = {"imagen": (os.path.basename(path), f, "application/octet-stream")}
        data = {"nombre": nombre, "email": email}
        headers = {"Authorization": f"Bearer {token}"}
        return requests.post(
            f"{API_URL}/api/personas",
            data=data, files=files, headers=headers, timeout=120,
        )


def main():
    if not os.path.isdir(REAL_DIR):
        print("No existe la carpeta:", REAL_DIR)
        sys.exit(1)

    token = login()

    imgs = sorted(
        p for p in glob.glob(os.path.join(REAL_DIR, "*"))
        if p.lower().endswith(VALID_EXT)
    )
    print(f"Se encontraron {len(imgs)} imagenes en realhumanos/\n")

    ok = skip = fail = 0
    for i, path in enumerate(imgs, 1):
        nombre = f"Persona {i}"
        email = f"realhumano{i}@dataset.local"
        name = os.path.basename(path)
        try:
            r = registrar(token, path, nombre, email)
            if r.status_code == 200:
                print(f"[OK]    {name}  ->  {nombre}")
                ok += 1
            elif r.status_code == 400 and "registrado" in r.text.lower():
                print(f"[YA]    {name}  (ya estaba registrado)")
                skip += 1
            elif r.status_code == 422:
                print(f"[SIN ROSTRO] {name}  (no se detecto un rostro claro)")
                fail += 1
            else:
                print(f"[FALLO {r.status_code}] {name}: {r.text[:150]}")
                fail += 1
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            fail += 1

    print(f"\nResumen: {ok} registradas, {skip} ya existian, {fail} con problema.")
    print("Ahora podras reconocerlas en la pestana Reconocimiento.")


if __name__ == "__main__":
    main()
