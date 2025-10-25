"""
Schemas Pydantic para gestión de usuarios.
Define la validación y serialización de datos para usuarios.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

from .validators import validate_phone_number
from src.shared.base_models import FilterParams


# ============================================
# SCHEMAS DE REQUEST
# ============================================

class CreateUsuarioRequest(BaseModel):
    """Schema para crear usuario (admin only)."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Contraseña inicial"
    )
    nombre: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Nombre completo"
    )
    telefono: Optional[str] = Field(
        None,
        max_length=20,
        description="Teléfono de contacto"
    )
    rol: str = Field(
        default="user",
        description="Rol del usuario (user/admin)"
    )
    activo: bool = Field(
        default=True,
        description="Si la cuenta está activa"
    )
    
    @field_validator("telefono")
    @classmethod
    def check_telefono(cls, v):
        """Valida formato de teléfono."""
        if v is None:
            return v
        
        is_valid, error_msg = validate_phone_number(v)
        if not is_valid:
            raise ValueError(error_msg)
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "nuevo@ejemplo.com",
                "password": "Password123",
                "nombre": "María García",
                "telefono": "+573001234567",
                "rol": "user",
                "activo": True
            }
        }


class UpdateUsuarioRequest(BaseModel):
    """Schema para actualizar usuario (admin only)."""
    
    nombre: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Nombre completo"
    )
    telefono: Optional[str] = Field(
        None,
        max_length=20,
        description="Teléfono de contacto"
    )
    rol: Optional[str] = Field(
        None,
        description="Rol del usuario (user/admin)"
    )
    activo: Optional[bool] = Field(
        None,
        description="Si la cuenta está activa"
    )
    
    @field_validator("telefono")
    @classmethod
    def check_telefono(cls, v):
        """Valida formato de teléfono."""
        if v is None:
            return v
        
        is_valid, error_msg = validate_phone_number(v)
        if not is_valid:
            raise ValueError(error_msg)
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "María García López",
                "telefono": "+573009876543",
                "activo": True
            }
        }


class UsuarioFilterParams(FilterParams):
    """Filtros específicos para búsqueda de usuarios."""
    
    rol: Optional[str] = Field(
        None,
        description="Filtrar por rol (user/admin)"
    )
    activo: Optional[bool] = Field(
        None,
        description="Filtrar por estado activo"
    )
    email_verificado: Optional[bool] = Field(
        None,
        description="Filtrar por email verificado"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "search": "juan",
                "activo": True,
                "rol": "user",
                "created_after": "2025-01-01T00:00:00Z"
            }
        }


# ============================================
# SCHEMAS DE RESPONSE
# ============================================

class UsuarioResponse(BaseModel):
    """Schema para respuesta con datos de usuario."""
    #cambien id:str por int
    id: int = Field(..., description="ID del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    telefono: Optional[str] = Field(None, description="Teléfono")
    email_verificado: bool = Field(..., description="Email verificado")
    activo: bool = Field(..., description="Cuenta activa")
    rol: str = Field(..., description="Rol del usuario (user/admin)")
    ultimo_login: Optional[datetime] = Field(None, description="Último login")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "usuario@ejemplo.com",
                "nombre": "Juan Pérez",
                "telefono": "+573001234567",
                "email_verificado": True,
                "activo": True,
                "rol": "user",
                "ultimo_login": "2025-10-07T10:30:00",
                "created_at": "2025-10-01T08:00:00",
                "updated_at": "2025-10-07T10:30:00"
            }
        }


class UsuarioStatsResponse(BaseModel):
    """Schema para estadísticas de usuarios."""
    
    total_usuarios: int = Field(..., description="Total de usuarios")
    usuarios_activos: int = Field(..., description="Usuarios activos")
    usuarios_inactivos: int = Field(..., description="Usuarios inactivos")
    emails_verificados: int = Field(..., description="Emails verificados")
    emails_sin_verificar: int = Field(..., description="Emails sin verificar")
    administradores: int = Field(..., description="Total de admins")
    usuarios_recientes: int = Field(
        ...,
        description="Usuarios registrados últimos 7 días"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_usuarios": 150,
                "usuarios_activos": 120,
                "usuarios_inactivos": 30,
                "emails_verificados": 100,
                "emails_sin_verificar": 50,
                "administradores": 5,
                "usuarios_recientes": 10
            }
        }
