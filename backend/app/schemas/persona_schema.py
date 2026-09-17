from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class PersonaCreate(BaseModel):
    nombre: str
    email: str


class PersonaResponse(BaseModel):
    id: UUID
    nombre: str
    email: str
    activo: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PersonaListResponse(BaseModel):
    success: bool
    personas: list[PersonaResponse]


class PersonaRegisterResponse(BaseModel):
    success: bool
    persona_id: UUID
    message: str = "Persona registrada exitosamente"
