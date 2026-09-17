import cv2
import numpy as np
from insightface.app import FaceAnalysis
from app.core.logging_config import logger


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
        logger.info("Initializing InsightFace FaceAnalysis model...")
        self.app = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        self._initialized = True
        logger.info("FaceAnalysis model loaded successfully")

    def detect_faces(self, image_bytes: bytes):
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
        return faces[0].embedding

    def get_embedding_with_quality(self, image_bytes: bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("No se pudo decodificar la imagen")

        faces = self.app.get(img)
        if not faces:
            raise ValueError("No se detectó ningún rostro en la imagen")

        face = faces[0]
        embedding = face.embedding
        bbox = face.bbox.astype(int)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        area_ratio = (w * h) / (img.shape[0] * img.shape[1])

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        quality = min(1.0, cv2.Laplacian(gray, cv2.CV_64F).var() / 500.0)
        illumination = float(np.mean(gray) / 255.0)

        return {
            "embedding": embedding,
            "quality": quality,
            "illumination": illumination,
            "area_ratio": area_ratio,
            "bbox": bbox.tolist(),
        }

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


face_service = FaceService()
