from pydantic import BaseModel, Field


class PrediccionInput(BaseModel):
    similitud: float = Field(..., ge=0.0, le=1.0)
    distancia: float = Field(..., ge=0.0, le=2.0)
    calidad_imagen: float = Field(..., ge=0.0, le=1.0)
    iluminacion: float = Field(..., ge=0.0, le=1.0)


class PrediccionResponse(BaseModel):
    success: bool
    probabilidad_calibrada: float


class TrainingRecordInput(BaseModel):
    similitud: float
    calidad_imagen: float
    iluminacion: float
    distancia: float
    resultado_real: bool


class TrainingRecordResponse(BaseModel):
    success: bool
    record_id: str
