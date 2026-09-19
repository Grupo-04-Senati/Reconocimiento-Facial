import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.connection import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
