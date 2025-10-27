"""
Schemas Pydantic para motos (DTOs).
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

from src.shared.base_models import FilterParams
from .validators import (
    validate_vin,
    validate_placa,
    validate_año,
    validate_kilometraje,
    validate_marca_ktm,
    validate_modelo,
)


# ==================== REQUEST SCHEMAS ====================

class RegisterMotoRequest(BaseModel):
    """Request para registrar una nueva moto."""
    
    vin: str = Field(..., description="VIN de 17 caracteres")
    modelo: str = Field(..., description="Modelo de la moto (ej: Duke 390)")
    año: int = Field(..., description="Año de fabricación")
    placa: Optional[str] = Field(None, description="Placa de la moto")
    color: Optional[str] = Field(None, max_length=50, description="Color de la moto")
    kilometraje: int = Field(default=0, ge=0, description="Kilometraje actual")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")
    
    # Validadores
    @field_validator("vin")
    @classmethod
    def validate_vin_field(cls, v: str) -> str:
        is_valid, error_msg = validate_vin(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip().upper()
    
    @field_validator("placa")
    @classmethod
    def validate_placa_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        is_valid, error_msg = validate_placa(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip().upper()
    
    @field_validator("año")
    @classmethod
    def validate_año_field(cls, v: int) -> int:
        is_valid, error_msg = validate_año(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("kilometraje")
    @classmethod
    def validate_kilometraje_field(cls, v: int) -> int:
        is_valid, error_msg = validate_kilometraje(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("modelo")
    @classmethod
    def validate_modelo_field(cls, v: str) -> str:
        is_valid, error_msg = validate_modelo(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip()


class UpdateMotoRequest(BaseModel):
    """Request para actualizar una moto (actualización parcial)."""
    
    placa: Optional[str] = Field(None, description="Nueva placa")
    color: Optional[str] = Field(None, max_length=50, description="Nuevo color")
    kilometraje: Optional[int] = Field(None, ge=0, description="Nuevo kilometraje")
    observaciones: Optional[str] = Field(None, description="Nuevas observaciones")
    
    # Validadores
    @field_validator("placa")
    @classmethod
    def validate_placa_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        is_valid, error_msg = validate_placa(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v.strip().upper()
    
    @field_validator("kilometraje")
    @classmethod
    def validate_kilometraje_field(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        is_valid, error_msg = validate_kilometraje(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UpdateKilometrajeRequest(BaseModel):
    """Request para actualizar solo el kilometraje."""
    
    kilometraje: int = Field(..., ge=0, description="Nuevo kilometraje")
    
    @field_validator("kilometraje")
    @classmethod
    def validate_kilometraje_field(cls, v: int) -> int:
        is_valid, error_msg = validate_kilometraje(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class MotoFilterParams(FilterParams):
    """Parámetros de filtrado para motos."""
    
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario")
    modelo: Optional[str] = Field(None, description="Filtrar por modelo (búsqueda parcial)")
    año_desde: Optional[int] = Field(None, description="Año de fabricación desde")
    año_hasta: Optional[int] = Field(None, description="Año de fabricación hasta")
    vin: Optional[str] = Field(None, description="Buscar por VIN")
    placa: Optional[str] = Field(None, description="Buscar por placa")
    
    # Ordenamiento
    order_by: Literal["id", "created_at", "año", "kilometraje", "modelo"] = Field(
        default="created_at",
        description="Campo para ordenar"
    )
    order_direction: Literal["asc", "desc"] = Field(
        default="desc",
        description="Dirección del ordenamiento"
    )
    
    # Validadores
    @field_validator("año_desde", "año_hasta")
    @classmethod
    def validate_año_field(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        is_valid, error_msg = validate_año(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


# ==================== RESPONSE SCHEMAS ====================

class UsuarioBasicInfo(BaseModel):
    """Información básica del usuario (para incluir en respuesta de moto)."""
    
    id: int
    nombre: str
    apellido: str
    email: str


class MotoResponse(BaseModel):
    """Response con información completa de una moto."""
    
    id: int
    usuario_id: int
    marca: str
    modelo: str
    año: int
    vin: str
    placa: Optional[str]
    color: Optional[str]
    kilometraje: int
    observaciones: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    
    # Relaciones
    usuario: Optional[UsuarioBasicInfo] = None
    
    # Propiedades computadas
    nombre_completo: Optional[str] = None
    es_ktm: Optional[bool] = None
    
    class Config:
        from_attributes = True


class MotoStatsResponse(BaseModel):
    """Response con estadísticas de motos."""
    
    total_motos: int
    motos_por_año: dict[int, int]
    kilometraje_promedio: float
    class ModeloPopular(BaseModel):
        modelo: str
        count: int

    modelos_populares: list[ModeloPopular]  # [{"modelo": "Duke 390", "count": 5}]


# ==================== COMPONENTE SCHEMAS ====================
from uuid import UUID
from typing import Dict, Any


class MotoComponenteCreate(BaseModel):
    moto_id: int
    tipo: str
    nombre: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class MotoComponenteUpdate(BaseModel):
    tipo: Optional[str] = None
    nombre: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class MotoComponenteRead(BaseModel):
    id: UUID
    moto_id: int
    tipo: str
    nombre: Optional[str] = None
    component_state: Optional[str] = None
    last_updated: Optional[datetime] = None
    extra_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
