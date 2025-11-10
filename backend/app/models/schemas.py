from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ----------- Auth / Usuarios -----------

class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    email: EmailStr
    telefono: Optional[str] = None
    password: str = Field(
        min_length=8,
        description="Contraseña del usuario (mínimo 8 caracteres). Soporta cualquier longitud gracias al pre-hash con SHA-256."
    )

class UsuarioOut(BaseModel):
    id: int
    nombres: str
    apellidos: str
    email: EmailStr
    estado: str
    class Config:
        from_attributes = True

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    session_id: str

class RefreshIn(BaseModel):
    session_id: str
    refresh_token: str

# ----------- Otros DTOs mínimos -----------

class ClienteCreate(BaseModel):
    nombre: str
    identificador: Optional[str] = None

class ClienteOut(BaseModel):
    id: int
    nombre: str
    identificador: Optional[str] = None
    estado: str
    class Config:
        from_attributes = True
