"""
Schemas Pydantic para sensores (DTOs).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.shared.base_models import FilterParams
from .models import EstadoSensor
from .validators import (
    validate_tipo_sensor,
    validate_codigo_sensor,
    validate_frecuencia_lectura,
    validate_umbrales,
    validate_valor_sensor,
    validate_timestamp_lectura
)


# ==================== REQUEST SCHEMAS ====================

class CreateSensorRequest(BaseModel):
    """Request para crear un sensor."""
    
    moto_id: int = Field(..., description="ID de la moto")
    tipo: str = Field(..., description="Tipo de sensor")
    codigo: str = Field(..., description="Código único del sensor")
    nombre: Optional[str] = Field(None, description="Nombre del sensor")
    ubicacion: Optional[str] = Field(None, description="Ubicación física")
    frecuencia_lectura: int = Field(5, ge=1, le=3600, description="Frecuencia en segundos")
    umbral_min: Optional[float] = Field(None, description="Umbral mínimo")
    umbral_max: Optional[float] = Field(None, description="Umbral máximo")
    fabricante: Optional[str] = Field(None, description="Fabricante")
    modelo: Optional[str] = Field(None, description="Modelo")
    version_firmware: Optional[str] = Field(None, description="Versión del firmware")
    notas: Optional[str] = Field(None, description="Notas")
    
    @field_validator("tipo")
    @classmethod
    def validate_tipo_field(cls, v: str) -> str:
        is_valid, error_msg = validate_tipo_sensor(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("codigo")
    @classmethod
    def validate_codigo_field(cls, v: str) -> str:
        is_valid, error_msg = validate_codigo_sensor(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("frecuencia_lectura")
    @classmethod
    def validate_frecuencia_field(cls, v: int) -> int:
        is_valid, error_msg = validate_frecuencia_lectura(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UpdateSensorRequest(BaseModel):
    """Request para actualizar un sensor."""
    
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    estado: Optional[str] = None
    frecuencia_lectura: Optional[int] = Field(None, ge=1, le=3600)
    umbral_min: Optional[float] = None
    umbral_max: Optional[float] = None
    version_firmware: Optional[str] = None
    notas: Optional[str] = None


class CreateLecturaRequest(BaseModel):
    """Request para registrar una lectura de sensor."""
    
    sensor_id: int = Field(..., description="ID del sensor")
    valor: float = Field(..., description="Valor de la lectura")
    timestamp_lectura: datetime = Field(..., description="Timestamp de la lectura")
    metadata_json: Optional[str] = Field(None, description="Metadata adicional (JSON)")
    
    @field_validator("timestamp_lectura")
    @classmethod
    def validate_timestamp_field(cls, v: datetime) -> datetime:
        is_valid, error_msg = validate_timestamp_lectura(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class SensorFilterParams(FilterParams):
    """Parámetros de filtrado para sensores."""
    
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    tipo: Optional[str] = Field(None, description="Filtrar por tipo de sensor")
    estado: Optional[str] = Field(None, description="Filtrar por estado")
    
    # Hereda de FilterParams:
    # - search: Optional[str]
    # - created_after: Optional[datetime]
    # - created_before: Optional[datetime]


class LecturaFilterParams(FilterParams):
    """Parámetros de filtrado para lecturas de sensores."""
    
    sensor_id: Optional[int] = Field(None, description="Filtrar por sensor")
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    fecha_inicio: Optional[datetime] = Field(None, description="Fecha inicio")
    fecha_fin: Optional[datetime] = Field(None, description="Fecha fin")
    fuera_rango: Optional[bool] = Field(None, description="Solo lecturas fuera de rango")
    
    # Hereda de FilterParams:
    # - search: Optional[str]
    # - created_after: Optional[datetime]
    # - created_before: Optional[datetime]


# ==================== RESPONSE SCHEMAS ====================

class SensorResponse(BaseModel):
    """Response con datos de sensor."""
    
    id: int
    moto_id: int
    tipo: str
    codigo: str
    nombre: Optional[str]
    ubicacion: Optional[str]
    estado: str
    frecuencia_lectura: int
    umbral_min: Optional[float]
    umbral_max: Optional[float]
    fabricante: Optional[str]
    modelo: Optional[str]
    version_firmware: Optional[str]
    ultima_lectura: Optional[datetime]
    ultima_calibracion: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class LecturaSensorResponse(BaseModel):
    """Response con datos de lectura."""
    
    id: int
    sensor_id: int
    valor: float
    unidad: str
    timestamp_lectura: datetime
    fuera_rango: bool
    alerta_generada: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class SensorStatsResponse(BaseModel):
    """Response con estadísticas de sensores."""
    
    total_sensores: int
    sensores_activos: int
    sensores_inactivos: int
    sensores_con_error: int
    lecturas_hoy: int
    alertas_hoy: int
    ultimas_lecturas: list[LecturaSensorResponse]
