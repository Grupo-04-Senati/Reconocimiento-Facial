from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class RecognitionResult(BaseModel):
    persona_id: UUID
    nombre: str
    similitud: float
    distancia: float
    umbral: float
    coincide: bool
    probabilidad_calibrada: Optional[float] = None


class RecognitionResponse(BaseModel):
    success: bool
    coincide: bool
    resultado: Optional[RecognitionResult] = None


class RecognitionLogEntry(BaseModel):
    id: UUID
    persona_id: Optional[UUID]
    similitud: float
    distancia: float
    umbral: float
    coincide: bool
    probabilidad_calibrada: Optional[float] = None
    created_at: str
    personas: Optional[dict] = None

    class Config:
        from_attributes = True


class HistorialResponse(BaseModel):
    success: bool
    historial: list[dict]
