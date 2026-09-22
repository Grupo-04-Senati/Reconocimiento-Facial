# -*- coding: utf-8 -*-
"""
Importa un dataset de Kaggle (rostros REALES y de IA) como DATOS INTERNOS de
entrenamiento para el clasificador Real vs IA por EMBEDDING (512 dims).

Que hace, imagen por imagen:
  descarga (kagglehub) -> detecta carpetas real / IA -> envia cada imagen al
  backend -> el backend detecta el rostro, calcula el embedding 512 y lo guarda
  en la tabla ml_face_samples (es_real true/false).

IMPORTANTE:
  - NO registra personas: estas imagenes son solo datos de entrenamiento, no
    aparecen en "registros" ni en la busqueda 1:N (tal como se pidio).
  - Requiere la migracion 013 aplicada en Supabase (crea ml_face_samples).
  - Corre en TU PC (usa tu backend por la API). El backend hace los embeddings.

--------------------------------------------------------------------------
COMO USARLO:

  1) Instala dependencias (una vez):
       pip install kagglehub requests

  2) Token de Kaggle (una vez). En tu cuenta Kaggle: Settings -> API ->
     "Create New Token" (descarga kaggle.json). Luego define en la terminal:
       PowerShell (Windows):
         $env:KAGGLE_USERNAME = "tu_usuario_kaggle"
         $env:KAGGLE_KEY      = "tu_api_key_kaggle"
     (o coloca kaggle.json en  C:/Users/<tu_usuario>/.kaggle/kaggle.json)

  3) Credenciales de admin de TU app (para subir por la API):
         $env:ADMIN_EMAIL    = "tu-correo@ejemplo.com"
         $env:ADMIN_PASSWORD = "tu-contrasena"
     (opcional, si tu backend no es el de Railway por defecto)
         $env:API_URL = "https://tu-backend"

  4) Ejecuta desde la raiz del proyecto:
       python scripts/importar_kaggle.py
     Opciones:
       python scripts/importar_kaggle.py --por-clase 150
       python scripts/importar_kaggle.py --dataset "kaustubhdhote/human-faces-dataset"
--------------------------------------------------------------------------
"""
import os
import sys
import glob
import argparse

try:
    import requests
except ImportError:
    print("Falta 'requests'. Instalalo con:  pip install kagglehub requests")
    sys.exit(1)

API_URL = os.environ.get(
    "API_URL", "https://reconocimiento-facial-production-1b3a.up.railway.app"
).rstrip("/")
EMAIL = os.environ.get("ADMIN_EMAIL", "")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

VALID_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

# Palabras clave para clasificar las carpetas del dataset.
AI_TERMS = ("ai", "fake", "gan", "generated", "generada", "synth", "sintetic",
            "artificial", "noreal", "no_real", "no-real", "falso", "falsa")
REAL_TERMS = ("real", "human", "humano", "genuine", "authentic", "verdad")


def login() -> str:
    if not EMAIL or not PASSWORD:
        print("ERROR: define ADMIN_EMAIL y ADMIN_PASSWORD como variables de entorno.")
        print('  PowerShell:  $env:ADMIN_EMAIL="correo"; $env:ADMIN_PASSWORD="clave"')
        sys.exit(1)
    print(f"Iniciando sesion en {API_URL} ...")
    r = requests.post(f"{API_URL}/api/auth/login",
                      json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        print(f"ERROR de login ({r.status_code}): {r.text[:200]}")
        sys.exit(1)
    token = r.json().get("token")
    if not token:
        print("ERROR: el login no devolvio token.")
        sys.exit(1)
    print("Login OK.\n")
    return token


def clasificar_carpeta(rel_path: str):
    """Devuelve 'ia', 'real' o None segun el nombre de la ruta."""
    low = rel_path.lower()
    if any(t in low for t in AI_TERMS):
        return "ia"
    if any(t in low for t in REAL_TERMS):
        return "real"
    return None


def agrupar_por_clase(root: str):
    """Recorre el dataset y agrupa las imagenes por clase (real / ia)."""
    grupos = {"real": [], "ia": []}
    sin_clasificar = {}
    for dirpath, _dirs, files in os.walk(root):
        imgs = [os.path.join(dirpath, f) for f in files if f.lower().endswith(VALID_EXT)]
        if not imgs:
            continue
        rel = os.path.relpath(dirpath, root)
        clase = clasificar_carpeta(rel)
        if clase:
            grupos[clase].extend(imgs)
        else:
            sin_clasificar[rel] = len(imgs)
    return grupos, sin_clasificar


def enviar(token: str, path: str, es_real: bool):
    with open(path, "rb") as f:
        files = {"imagen": (os.path.basename(path), f, "application/octet-stream")}
        headers = {"Authorization": f"Bearer {token}"}
        params = {"es_real": "true" if es_real else "false", "fuente": "kaggle"}
        return requests.post(f"{API_URL}/api/modelos/muestra-embedding",
                             files=files, params=params, headers=headers, timeout=120)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="kaustubhdhote/human-faces-dataset",
                    help="slug del dataset en Kaggle")
    ap.add_argument("--por-clase", type=int, default=150,
                    help="cuantas imagenes importar por clase (real / ia)")
    ap.add_argument("--email", default="",
                    help="correo de admin (alternativa a la variable ADMIN_EMAIL)")
    ap.add_argument("--password", default="",
                    help="clave de admin (alternativa a la variable ADMIN_PASSWORD)")
    args = ap.parse_args()

    # Las credenciales por --email/--password evitan pelear con la sintaxis del
    # shell (CMD usa 'set', PowerShell usa '$env:'). Si se pasan, tienen prioridad.
    global EMAIL, PASSWORD
    if args.email:
        EMAIL = args.email
    if args.password:
        PASSWORD = args.password

    try:
        import kagglehub
    except ImportError:
        print("Falta 'kagglehub'. Instalalo con:  pip install kagglehub")
        sys.exit(1)

    print(f"Descargando dataset '{args.dataset}' de Kaggle ...")
    print("(la primera vez puede tardar; requiere tu token de Kaggle)\n")
    try:
        root = kagglehub.dataset_download(args.dataset)
    except Exception as e:
        print(f"ERROR descargando de Kaggle: {e}")
        print("Revisa tu token (KAGGLE_USERNAME/KAGGLE_KEY o ~/.kaggle/kaggle.json).")
        sys.exit(1)
    print("Descargado en:", root, "\n")

    grupos, sin_clasificar = agrupar_por_clase(root)
    print(f"Detectado: {len(grupos['real'])} imagenes REAL, {len(grupos['ia'])} imagenes IA")
    if sin_clasificar:
        print("Carpetas NO clasificadas (se omiten; renombralas si son real/ia):")
        for rel, n in list(sin_clasificar.items())[:10]:
            print(f"   - {rel}  ({n} imgs)")
    if not grupos["real"] or not grupos["ia"]:
        print("\nAVISO: falta alguna de las dos clases (real / ia). El ML necesita AMBAS.")
        print("Si el dataset solo trae una clase, complementa con imagenes de la otra.")
        if not grupos["real"] and not grupos["ia"]:
            sys.exit(1)

    token = login()

    total_ok = total_skip = total_fail = 0
    for clase, es_real in (("real", True), ("ia", False)):
        imgs = sorted(grupos[clase])[: args.por_clase]
        if not imgs:
            continue
        print(f"\n=== Subiendo {len(imgs)} imagenes de clase '{clase}' ===")
        for i, path in enumerate(imgs, 1):
            name = os.path.basename(path)
            try:
                r = enviar(token, path, es_real)
                if r.status_code == 200:
                    total_ok += 1
                    if i % 25 == 0 or i == len(imgs):
                        print(f"  [{i}/{len(imgs)}] OK ... ({name})")
                elif r.status_code == 422:
                    total_skip += 1  # sin rostro detectable
                else:
                    total_fail += 1
                    print(f"  [FALLO {r.status_code}] {name}: {r.text[:120]}")
            except Exception as e:
                total_fail += 1
                print(f"  [ERROR] {name}: {e}")

    print(f"\nResumen: {total_ok} muestras guardadas, {total_skip} sin rostro (omitidas), "
          f"{total_fail} con error.")
    print("Ahora ve a 'Entrenamiento ML' y pulsa Entrenar: el modelo aprendera del")
    print("embedding (pixeles) para distinguir Humano Real vs IA.")


if __name__ == "__main__":
    main()
