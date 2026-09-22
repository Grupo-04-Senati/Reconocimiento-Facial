import numpy as np
import math
from app.core.logging_config import logger

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python no instalado. Detección de rostros deshabilitada.")

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logger.warning("insightface no instalado. Detección de rostros deshabilitada.")


class FaceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.app = None
        if INSIGHTFACE_AVAILABLE and CV2_AVAILABLE:
            try:
                logger.info("Initializing InsightFace FaceAnalysis model...")
                import os

                model_root = "/root/.insightface"
                if not os.path.exists(os.path.join(model_root, "models", "buffalo_s")):
                    model_root = None

                self.app = FaceAnalysis(
                    name="buffalo_s",
                    root=model_root,
                    providers=["CPUExecutionProvider"],
                )
                self.app.prepare(ctx_id=0, det_size=(640, 640))

                self._initialized = True
                logger.info("FaceAnalysis model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load InsightFace model: {e}")
        else:
            logger.warning("Face detection disabled - missing dependencies")

    def _check_dependencies(self):
        if not CV2_AVAILABLE:
            raise ImportError("opencv-python-headless no está instalado. Ejecuta: pip install opencv-python-headless")
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError("insightface no está instalado. Ejecuta: pip install insightface onnxruntime")
        if self.app is None:
            raise RuntimeError("Modelo de detección facial no inicializado")

    def detect_faces(self, image_bytes: bytes):
        self._check_dependencies()
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("No se pudo decodificar la imagen")
        faces = self.app.get(img)
        if not faces:
            raise ValueError("No se detectó ningún rostro en la imagen")
        return faces

    def get_embedding(self, image_bytes: bytes) -> np.ndarray:
        faces = self.detect_faces(image_bytes)
        embedding = faces[0].normed_embedding
        norm = np.linalg.norm(embedding)
        print(f"[face_service] get_embedding: norm={norm:.4f}")
        return embedding

    def get_embedding_with_quality(self, image_bytes: bytes):
        self._check_dependencies()
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("No se pudo decodificar la imagen")

        faces = self.app.get(img)
        if not faces:
            raise ValueError("No se detectó ningún rostro en la imagen")

        face = faces[0]
        embedding = face.normed_embedding
        norm = np.linalg.norm(embedding)
        print(f"[face_service] get_embedding_with_quality: norm={norm:.4f}")
        bbox = face.bbox.astype(int)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        area_ratio = (w * h) / (img.shape[0] * img.shape[1])

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        quality = min(1.0, cv2.Laplacian(gray, cv2.CV_64F).var() / 500.0)
        illumination = float(np.mean(gray) / 255.0)

        opencv_features = self.extract_opencv_features(img, gray)

        return {
            "embedding": embedding,
            "quality": quality,
            "illumination": illumination,
            "area_ratio": area_ratio,
            "bbox": bbox.tolist(),
            **opencv_features,
        }

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    @staticmethod
    def extract_opencv_features(img: np.ndarray, gray: np.ndarray) -> dict:
        """Extrae features OpenCV para detectar AI vs Humano (16 features).

        Features:
        - textura: varianza del Laplaciano (AI tiene piel mas suave)
        - frecuencia_baja: promedio FFT en bajas frecuencias
        - frecuencia_alta: promedio FFT en altas frecuencias
        - fft_varianza: varianza del espectro FFT (AI tiene espectro mas uniforme)
        - ruido: desviacion estandar de imagen original vs suavizada
        - contraste_textura: desviacion estandar del Laplaciano
        - asimetria: diferencia entre mitad izquierda y derecha
        - brillo_variacion: varianza del brillo
        - edge_consistency: coherencia de bordes
        - lbp_mean: patron binario local promedio (textura piel)
        - lbp_var: varianza del LBP (AI tiene patron mas uniforme)
        - lbp_contraste: contraste del LBP
        - freq_edge_mean: frecuencia en bordes del espectro
        - freq_edge_var: varianza en bordes del espectro
        - entropy: entropia de la imagen (complejidad textural)
        - skin_smoothness: suavidad de piel (AI mas suave)
        """
        features = {}
        h, w = gray.shape

        # Textura: varianza del Laplaciano
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        features["textura"] = float(min(1.0, laplacian.var() / 500.0))
        features["contraste_textura"] = float(min(1.0, laplacian.std() / 200.0))

        # FFT: analisis de frecuencia mejorado
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
            if mask_high.any():
                features["frecuencia_alta"] = float(np.mean(magnitude[mask_high]) / 10.0)
            else:
                features["frecuencia_alta"] = 0.0

            features["fft_varianza"] = float(min(1.0, np.std(magnitude) / 5.0))
        except Exception:
            features["frecuencia_baja"] = 0.5
            features["frecuencia_alta"] = 0.5
            features["fft_varianza"] = 0.5
            features["freq_edge_mean"] = 0.5
            features["freq_edge_var"] = 0.5

        for k in ["frecuencia_baja", "frecuencia_alta", "fft_varianza", "freq_edge_mean", "freq_edge_var"]:
            features[k] = max(0.0, min(1.0, features[k]))

        # Ruido
        try:
            blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
            noise = np.std(gray.astype(np.float32) - blurred.astype(np.float32))
            features["ruido"] = float(min(1.0, noise / 30.0))
        except Exception:
            features["ruido"] = 0.5

        # Asimetria
        try:
            left_half = gray[:, :w//2]
            right_half = cv2.flip(gray[:, w//2:], 1)
            min_w = min(left_half.shape[1], right_half.shape[1])
            diff = np.abs(left_half[:, :min_w].astype(np.float32) - right_half[:, :min_w].astype(np.float32))
            features["asimetria"] = float(min(1.0, np.mean(diff) / 50.0))
        except Exception:
            features["asimetria"] = 0.5

        # Brillo
        try:
            features["brillo_variacion"] = float(min(1.0, np.std(gray.astype(np.float32)) / 80.0))
        except Exception:
            features["brillo_variacion"] = 0.5

        # Bordes
        try:
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (h * w)
            features["edge_consistency"] = float(min(1.0, edge_density))
        except Exception:
            features["edge_consistency"] = 0.5

        # LBP: Local Binary Patterns (microtexturas de piel)
        try:
            radius_lbp = 1
            n_points = 8 * radius_lbp
            lbp = np.zeros_like(gray, dtype=np.uint8)
            for i in range(radius_lbp, h - radius_lbp):
                for j in range(radius_lbp, w - radius_lbp):
                    center = gray[i, j]
                    code = 0
                    for k, (dy, dx) in enumerate([
                        (-1, -1), (-1, 0), (-1, 1), (0, 1),
                        (1, 1), (1, 0), (1, -1), (0, -1)
                    ]):
                        if gray[i + dy, j + dx] >= center:
                            code |= (1 << k)
                    lbp[i, j] = code
            features["lbp_mean"] = float(min(1.0, np.mean(lbp) / 255.0))
            features["lbp_var"] = float(min(1.0, np.std(lbp) / 128.0))
            hist, _ = np.histogram(lbp, bins=16, range=(0, 256), density=True)
            features["lbp_contraste"] = float(min(1.0, np.sum(hist ** 2)))
        except Exception:
            features["lbp_mean"] = 0.5
            features["lbp_var"] = 0.5
            features["lbp_contraste"] = 0.5

        # Entropia: complejidad textural
        try:
            hist_gray, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
            hist_gray = hist_gray[hist_gray > 0]
            features["entropy"] = float(min(1.0, -np.sum(hist_gray * np.log2(hist_gray)) / 8.0))
        except Exception:
            features["entropy"] = 0.5

        # Suavidad de piel: ratio de energia Laplaciano vs imagen
        try:
            lap_energy = np.sum(laplacian ** 2)
            img_energy = np.sum(gray.astype(np.float64) ** 2) + 1e-10
            features["skin_smoothness"] = float(min(1.0, 1.0 - (lap_energy / img_energy)))
        except Exception:
            features["skin_smoothness"] = 0.5

        return features


face_service = FaceService()
