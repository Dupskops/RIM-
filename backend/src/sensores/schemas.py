"""
Schemas Pydantic para el módulo de sensores.

DTOs para API REST y WebSocket:
- Templates: SensorTemplateCreate, SensorTemplateUpdate, SensorTemplateRead
- Sensores: CreateSensorRequest, UpdateSensorRequest, SensorRead
- Lecturas: CreateLecturaRequest, LecturaRead
- Filtros y respuestas: SensorFilters, LecturaFilters, SensorStatsResponse
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from .models import SensorState
from ..motos.models import ComponentState


# ============================================
# SENSOR TEMPLATES
# ============================================

class SensorTemplateCreate(BaseModel):
    """Request para crear plantilla de sensor."""
    modelo: str = Field(..., max_length=128, description="Modelo de moto")
    name: str = Field(..., max_length=128, description="Nombre descriptivo del sensor")
    definition: Dict[str, Any] = Field(
        ...,
        description="Definición JSONB con sensor_type, unit, thresholds, frequency_ms, component_type"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "modelo": "Ducati Panigale V4",
                "name": "Temperatura Motor",
                "definition": {
                    "sensor_type": "temperature",
                    "unit": "celsius",
                    "default_thresholds": {"min": 0, "max": 120},
                    "frequency_ms": 1000,
                    "component_type": "engine"
                }
            }
        }
    )


class SensorTemplateUpdate(BaseModel):
    """Request para actualizar plantilla de sensor."""
    name: Optional[str] = Field(None, max_length=128)
    definition: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Temp Motor (Actualizado)",
                "definition": {
                    "sensor_type": "temperature",
                    "unit": "celsius",
                    "default_thresholds": {"min": 10, "max": 110},
                    "frequency_ms": 500,
                    "component_type": "engine"
                }
            }
        }
    )


class SensorTemplateRead(BaseModel):
    """Response con plantilla de sensor."""
    id: UUID
    modelo: str
    name: str
    definition: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SENSORES
# ============================================

class CreateSensorRequest(BaseModel):
    """Request para registrar sensor manualmente."""
    moto_id: int = Field(..., description="ID de la moto (int FK)")
    template_id: Optional[UUID] = Field(None, description="Plantilla base (opcional)")
    nombre: Optional[str] = Field(None, max_length=128, description="Nombre descriptivo")
    tipo: str = Field(..., max_length=64, description="Tipo de sensor (temperature, pressure, etc)")
    componente_id: Optional[UUID] = Field(None, description="Componente físico asociado")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuración personalizada (thresholds, calibration)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "moto_id": 1,
                "template_id": "223e4567-e89b-12d3-a456-426614174111",
                "nombre": "Temp Motor Principal",
                "tipo": "temperature",
                "componente_id": "323e4567-e89b-12d3-a456-426614174222",
                "config": {
                    "thresholds": {"min": 20, "max": 100},
                    "calibration_offset": 0.5,
                    "enabled": True
                }
            }
        }
    )


class UpdateSensorRequest(BaseModel):
    """Request para actualizar sensor."""
    nombre: Optional[str] = Field(None, max_length=128)
    sensor_state: Optional[SensorState] = None
    config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Temp Motor Principal (Calibrado)",
                "sensor_state": "ok",
                "config": {
                    "thresholds": {"min": 15, "max": 105},
                    "calibration_offset": 0.3,
                    "enabled": True
                }
            }
        }
    )


class SensorRead(BaseModel):
    """Response con sensor."""
    id: UUID
    moto_id: int
    template_id: Optional[UUID]
    nombre: Optional[str]
    tipo: str
    componente_id: Optional[UUID]
    config: Dict[str, Any]
    sensor_state: SensorState
    last_value: Optional[Dict[str, Any]]
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# LECTURAS
# ============================================

class CreateLecturaRequest(BaseModel):
    """Request para registrar lectura de sensor."""
    sensor_id: UUID
    ts: datetime = Field(..., description="Timestamp de la lectura")
    valor: Dict[str, Any] = Field(
        ...,
        description="Valor JSONB con value, unit, raw (opcional)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata adicional: quality, anomaly_score, source"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "423e4567-e89b-12d3-a456-426614174333",
                "ts": "2025-10-26T10:30:00Z",
                "valor": {
                    "value": 78.5,
                    "unit": "celsius",
                    "raw": 785
                },
                "metadata": {
                    "quality": 0.99,
                    "anomaly_score": 0.02,
                    "source": "websocket"
                }
            }
        }
    )


class LecturaRead(BaseModel):
    """Response con lectura."""
    id: int
    moto_id: int
    sensor_id: UUID
    component_id: Optional[UUID]
    ts: datetime
    valor: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# FILTROS
# ============================================

class SensorFilters(BaseModel):
    """Filtros para listar sensores."""
    moto_id: Optional[int] = None
    tipo: Optional[str] = None
    sensor_state: Optional[SensorState] = None
    componente_id: Optional[UUID] = None


class LecturaFilters(BaseModel):
    """Filtros para listar lecturas."""
    moto_id: Optional[int] = None
    sensor_id: Optional[UUID] = None
    component_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ============================================
# RESPONSES
# ============================================

class SensorStatsResponse(BaseModel):
    """Estadísticas de sensores por estado."""
    total: int = Field(..., description="Total de sensores")
    ok: int = Field(default=0, description="Sensores en estado OK")
    degraded: int = Field(default=0, description="Sensores degradados")
    faulty: int = Field(default=0, description="Sensores con fallas")
    offline: int = Field(default=0, description="Sensores offline")
    unknown: int = Field(default=0, description="Sensores en estado desconocido")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 12,
                "ok": 10,
                "degraded": 1,
                "faulty": 0,
                "offline": 1,
                "unknown": 0
            }
        }
    )


class ComponentStateResponse(BaseModel):
    """Response de estado de componente."""
    componente_id: UUID
    moto_id: int
    tipo: str
    nombre: Optional[str]
    component_state: ComponentState
    sensor_count: int
    last_updated: Optional[datetime]
    aggregation_data: Dict[str, Any]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "componente_id": "323e4567-e89b-12d3-a456-426614174222",
                "moto_id": 1,
                "tipo": "engine",
                "nombre": "Motor Principal",
                "component_state": "ok",
                "sensor_count": 3,
                "last_updated": "2025-10-26T10:30:00Z",
                "aggregation_data": {
                    "max_sensor_score": 0,
                    "sensor_states": {"ok": 3},
                    "anomaly_count": 0
                }
            }
        }
    )
