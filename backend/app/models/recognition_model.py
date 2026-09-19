import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="SET NULL"))
    similitud = Column(Float, nullable=False)
    distancia = Column(Float, nullable=False)
    umbral = Column(Float, nullable=False)
    coincide = Column(Boolean, nullable=False)
    probabilidad_calibrada = Column(Float)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    embedding = Column(String, nullable=False)
    modelo = Column(String, nullable=False, default="arcface")
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
