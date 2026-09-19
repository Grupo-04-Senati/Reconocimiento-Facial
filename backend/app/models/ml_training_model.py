import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class MLTrainingRecord(Base):
    __tablename__ = "ml_training_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    similitud = Column(Float, nullable=False)
    calidad_imagen = Column(Float, nullable=False)
    iluminacion = Column(Float, nullable=False)
    distancia = Column(Float, nullable=False)
    resultado_real = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
