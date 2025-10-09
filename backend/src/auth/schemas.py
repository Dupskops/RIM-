"""
Schemas Pydantic para autenticación.
Define la validación y serialización de datos para auth.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date

from .validators import validate_password_strength, validate_phone_number
from ..shared.base_models import FilterParams


# ============================================
# SCHEMAS DE REQUEST
# ============================================

class RegisterRequest(BaseModel):
    """Schema para registro de nuevo usuario."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Contraseña (mínimo 8 caracteres)"
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
    
    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v):
        """Valida que la contraseña sea fuerte."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
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
                "email": "usuario@ejemplo.com",
                "password": "MiPassword123",
                "nombre": "Juan Pérez",
                "telefono": "+573001234567"
            }
        }


class LoginRequest(BaseModel):
    """Schema para login de usuario."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com",
                "password": "MiPassword123"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema para renovar access token con refresh token."""
    
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Schema para cambiar contraseña (usuario autenticado)."""
    
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nueva contraseña"
    )
    
    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v):
        """Valida que la nueva contraseña sea fuerte."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "MiPassword123",
                "new_password": "NuevoPassword456"
            }
        }


class RequestPasswordResetRequest(BaseModel):
    """Schema para solicitar reset de contraseña."""
    
    email: EmailStr = Field(..., description="Email del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Schema para resetear contraseña con token."""
    
    token: str = Field(..., description="Token de reseteo")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Nueva contraseña"
    )
    
    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v):
        """Valida que la nueva contraseña sea fuerte."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456",
                "new_password": "NuevoPassword789"
            }
        }


class VerifyEmailRequest(BaseModel):
    """Schema para verificar email con token."""
    
    token: str = Field(..., description="Token de verificación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "xyz789abc123"
            }
        }


class UpdateProfileRequest(BaseModel):
    """Schema para actualizar perfil de usuario."""
    
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
                "nombre": "Juan Carlos Pérez",
                "telefono": "+573009876543"
            }
        }


# ============================================
# SCHEMAS DE RESPONSE
# ============================================

class TokenResponse(BaseModel):
    """Schema para respuesta con tokens JWT."""
    
    access_token: str = Field(..., description="Access token JWT")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta expiración")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class UserResponse(BaseModel):
    """Schema para respuesta con datos de usuario."""
    
    id: str = Field(..., description="ID del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo")
    telefono: Optional[str] = Field(None, description="Teléfono")
    email_verificado: bool = Field(..., description="Email verificado")
    activo: bool = Field(..., description="Cuenta activa")
    rol: str = Field(..., description="Rol del usuario (user/admin)")
    ultimo_login: Optional[datetime] = Field(None, description="Último login")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Última actualización")
    
    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_string(cls, v):
        """Convierte el ID a string si es necesario."""
        return str(v) if v is not None else v
    
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
                "es_admin": False,
                "ultimo_login": "2025-10-07T10:30:00",
                "created_at": "2025-10-01T08:00:00",
                "updated_at": "2025-10-07T10:30:00"
            }
        }


class LoginResponse(BaseModel):
    """Schema para respuesta de login exitoso."""
    
    user: UserResponse = Field(..., description="Datos del usuario")
    tokens: TokenResponse = Field(..., description="Tokens de autenticación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "usuario@ejemplo.com",
                    "nombre": "Juan Pérez",
                    "email_verificado": True,
                    "activo": True,
                    "es_admin": False
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                }
            }
        }


class MessageResponse(BaseModel):
    """Schema para respuestas simples con mensaje."""
    
    message: str = Field(..., description="Mensaje de respuesta")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operación exitosa"
            }
        }


class TokenValidationResponse(BaseModel):
    """Schema para respuesta de validación de token."""
    
    valid: bool = Field(..., description="Si el token es válido")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "usuario@ejemplo.com",
                "expires_at": "2025-10-07T11:30:00"
            }
        }
