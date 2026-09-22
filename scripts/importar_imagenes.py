"""
Script para importar imágenes y generar features OpenCV reales.
Uso:
  python importar_imagenes.py --real "C:/fotos/reales" --fake "C:/fotos/ia"

Cada carpeta debe contener imágenes de rostros (JPG/PNG).
  - --real: fotos de personas reales (humano_real)
  - --fake: fotos generadas por IA (no_real)
"""
import os
import sys
import argparse
import httpx
import cv2
import numpy as np
from pathlib import Path

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://guzdgiqfqqbuetbpickr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

IMAGES_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def extract_opencv_features(img: np.ndarray, gray: np.ndarray) -> dict:
    features = {}
    h, w = gray.shape

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    features["textura"] = float(min(1.0, laplacian.var() / 500.0))
    features["contraste_textura"] = float(min(1.0, laplacian.std() / 200.0))

    try:
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = np.log(np.abs(fshift) + 1)
        cy, cx = h // 2, w // 2
        radius = min(cy, cx) // 3
        y, x = np.ogrid[:h, :w]
        mask_low = (y - cy)**2 + (x - cx)**2 <= radius**2
        features["frecuencia_baja"] = float(np.mean(magnitude[mask_low]) / 10.0)
        mask_mid = ((y - cy)**2 + (x - cx)**2 > radius**2) & ((y - cy)**2 + (x - cx)**2 <= (radius * 2)**2)
        features["freq_edge_mean"] = float(np.mean(magnitude[mask_mid]) / 10.0) if mask_mid.any() else 0.5
        features["freq_edge_var"] = float(np.std(magnitude[mask_mid]) / 10.0) if mask_mid.any() else 0.5
        mask_high = (y - cy)**2 + (x - cx)**2 > (radius * 2)**2
        features["frecuencia_alta"] = float(np.mean(magnitude[mask_high]) / 10.0) if mask_high.any() else 0.0
        features["fft_varianza"] = float(min(1.0, np.std(magnitude) / 5.0))
    except Exception:
        for k in ["frecuencia_baja", "frecuencia_alta", "fft_varianza", "freq_edge_mean", "freq_edge_var"]:
            features[k] = 0.5

    for k in ["frecuencia_baja", "frecuencia_alta", "fft_varianza", "freq_edge_mean", "freq_edge_var"]:
        features[k] = max(0.0, min(1.0, features[k]))

    try:
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
        noise = np.std(gray.astype(np.float32) - blurred.astype(np.float32))
        features["ruido"] = float(min(1.0, noise / 30.0))
    except Exception:
        features["ruido"] = 0.5

    try:
        left_half = gray[:, :w//2]
        right_half = cv2.flip(gray[:, w//2:], 1)
        min_w = min(left_half.shape[1], right_half.shape[1])
        diff = np.abs(left_half[:, :min_w].astype(np.float32) - right_half[:, :min_w].astype(np.float32))
        features["asimetria"] = float(min(1.0, np.mean(diff) / 50.0))
    except Exception:
        features["asimetria"] = 0.5

    try:
        features["brillo_variacion"] = float(min(1.0, np.std(gray.astype(np.float32)) / 80.0))
    except Exception:
        features["brillo_variacion"] = 0.5

    try:
        edges = cv2.Canny(gray, 50, 150)
        features["edge_consistency"] = float(min(1.0, np.sum(edges > 0) / (h * w)))
    except Exception:
        features["edge_consistency"] = 0.5

    try:
        radius_lbp = 1
        lbp = np.zeros_like(gray, dtype=np.uint8)
        for i in range(radius_lbp, h - radius_lbp):
            for j in range(radius_lbp, w - radius_lbp):
                center = gray[i, j]
                code = 0
                for k_idx, (dy, dx) in enumerate([(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]):
                    if gray[i + dy, j + dx] >= center:
                        code |= (1 << k_idx)
                lbp[i, j] = code
        features["lbp_mean"] = float(min(1.0, np.mean(lbp) / 255.0))
        features["lbp_var"] = float(min(1.0, np.std(lbp) / 128.0))
        hist, _ = np.histogram(lbp, bins=16, range=(0, 256), density=True)
        features["lbp_contraste"] = float(min(1.0, np.sum(hist ** 2)))
    except Exception:
        features["lbp_mean"] = 0.5
        features["lbp_var"] = 0.5
        features["lbp_contraste"] = 0.5

    try:
        hist_gray, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
        hist_gray = hist_gray[hist_gray > 0]
        features["entropy"] = float(min(1.0, -np.sum(hist_gray * np.log2(hist_gray)) / 8.0))
    except Exception:
        features["entropy"] = 0.5

    try:
        lap_energy = np.sum(laplacian ** 2)
        img_energy = np.sum(gray.astype(np.float64) ** 2) + 1e-10
        features["skin_smoothness"] = float(min(1.0, 1.0 - (lap_energy / img_energy)))
    except Exception:
        features["skin_smoothness"] = 0.5

    return features


def extract_embedding(image_bytes: bytes) -> list:
    """Extrae embedding 512-dim usando InsightFace."""
    import insightface
    from app.services.face_service import face_service

    if not face_service._initialized:
        print("Inicializando face_service...")
        face_service._init_model()

    faces = face_service.app.get(cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR))
    if not faces:
        return None

    emb = faces[0].embedding
    return emb.tolist() if hasattr(emb, "tolist") else list(emb)


def process_folder(folder: str, es_real: bool) -> list:
    """Procesa todas las imágenes de una carpeta."""
    results = []
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"ERROR: Carpeta no existe: {folder}")
        return results

    files = [f for f in folder_path.iterdir() if f.suffix.lower() in IMAGES_EXTS]
    print(f"\nProcesando {len(files)} imágenes de {folder} (es_real={es_real})")

    for i, file_path in enumerate(files):
        try:
            img = cv2.imread(str(file_path))
            if img is None:
                print(f"  [{i+1}/{len(files)}] SKIP: No se pudo leer {file_path.name}")
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            features = extract_opencv_features(img, gray)

            with open(file_path, "rb") as f:
                image_bytes = f.read()

            embedding = extract_embedding(image_bytes)

            if embedding is None:
                print(f"  [{i+1}/{len(files)}] SKIP: No se detectó rostro en {file_path.name}")
                continue

            results.append({
                "features": features,
                "embedding": embedding,
                "es_real": es_real,
                "nombre": file_path.name,
            })
            print(f"  [{i+1}/{len(files)}] OK: {file_path.name} - textura={features['textura']:.3f}, ruido={features['ruido']:.3f}")

        except Exception as e:
            print(f"  [{i+1}/{len(files)}] ERROR: {file_path.name}: {e}")

    return results


def insert_to_db(records: list):
    """Inserta registros en ml_training_records via PostgREST."""
    if not records:
        print("\nNo hay registros para insertar.")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    payload = []
    for r in records:
        import json
        row = {
            "similitud": 1.0 if r["es_real"] else 0.3,
            "distancia": 0.0 if r["es_real"] else 0.7,
            "calidad_imagen": 0.8,
            "iluminacion": 0.8,
            "resultado_real": r["es_real"],
            "fuente": "importacion_local",
            "textura": r["features"]["textura"],
            "frecuencia_baja": r["features"]["frecuencia_baja"],
            "frecuencia_alta": r["features"]["frecuencia_alta"],
            "ruido": r["features"]["ruido"],
            "contraste_textura": r["features"]["contraste_textura"],
            "asimetria": r["features"]["asimetria"],
            "brillo_variacion": r["features"]["brillo_variacion"],
            "edge_consistency": r["features"]["edge_consistency"],
            "embedding": json.dumps(r["embedding"]),
        }
        payload.append(row)

    with httpx.Client() as client:
        resp = client.post(
            f"{SUPABASE_URL}/rest/v1/ml_training_records",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code in (200, 201):
            print(f"\nInsertados {len(payload)} registros en ml_training_records")
        else:
            print(f"\nERROR al insertar: {resp.status_code} {resp.text[:300]}")


def main():
    parser = argparse.ArgumentParser(description="Importar imágenes al modelo ML")
    parser.add_argument("--real", type=str, help="Carpeta con fotos de personas reales")
    parser.add_argument("--fake", type=str, help="Carpeta con fotos generadas por IA")
    parser.add_argument("--url", type=str, help="Supabase URL", default=SUPABASE_URL)
    parser.add_argument("--key", type=str, help="Supabase Service Role Key", default=SUPABASE_KEY)
    args = parser.parse_args()

    global SUPABASE_URL, SUPABASE_KEY
    SUPABASE_URL = args.url
    SUPABASE_KEY = args.key

    if not SUPABASE_KEY:
        print("ERROR: Debes proporcionar --key o setear SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    all_records = []

    if args.real:
        all_records.extend(process_folder(args.real, es_real=True))

    if args.fake:
        all_records.extend(process_folder(args.fake, es_real=False))

    if not all_records:
        print("\nNo se procesaron imágenes. Usa --real y/o --fake con rutas a carpetas.")
        sys.exit(1)

    print(f"\nTotal: {len(all_records)} imágenes procesadas")
    insert_to_db(all_records)


if __name__ == "__main__":
    main()
