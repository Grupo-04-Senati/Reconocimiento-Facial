"""
Download pre-trained models for the Facial Recognition System.

This script downloads the required ONNX models for InsightFace.
Run this script after setting up the backend environment.

Usage:
    python scripts/download_models.py
"""

import os
import sys
import urllib.request

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "models")

MODELS = {
    "arcface.onnx": {
        "description": "ArcFace model for face embedding generation",
        "size": "~250MB",
    },
}


def download_model(name: str, url: str):
    dest = os.path.join(MODEL_DIR, name)
    os.makedirs(MODEL_DIR, exist_ok=True)

    if os.path.exists(dest):
        print(f"  [SKIP] {name} already exists")
        return

    print(f"  Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [OK] {name} downloaded")
    except Exception as e:
        print(f"  [ERROR] Failed to download {name}: {e}")
        print(f"  Please download manually and place in {MODEL_DIR}")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  Model Downloader - Facial Recognition System")
    print("=" * 50)
    print()
    print("Models directory:", os.path.abspath(MODEL_DIR))
    print()

    for name, info in MODELS.items():
        print(f"Model: {name}")
        print(f"  Description: {info['description']}")
        print(f"  Size: {info['size']}")

    print()
    print("Note: InsightFace models (buffalo_l) are downloaded")
    print("automatically on first use by the insightface library.")
    print()
    print("To download buffalo_l model manually:")
    print("  pip install insightface")
    print("  python -c \"from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l')\"")

    os.makedirs(MODEL_DIR, exist_ok=True)
    print()
    print("Setup complete! Models directory ready.")


if __name__ == "__main__":
    main()
