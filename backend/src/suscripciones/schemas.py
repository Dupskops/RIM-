"""
Schemas Pydantic para suscripciones (DTOs).
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

from src.shared.base_models import FilterParams
from .models import PlanType
from .validators import (
    validate_plan,
    validate_status,
    validate_date_range,
    validate_precio,
    validate_metodo_pago,
    validate_duracion
)


# ==================== REQUEST SCHEMAS ====================

class CreateSuscripcionRequest(BaseModel):
    """Request para crear una nueva suscripción."""
    
    usuario_id: int = Field(..., description="ID del usuario (INTEGER)")
    plan: str = Field(..., description="Tipo de plan (freemium/premium)")
    duracion_meses: Optional[int] = Field(
        None,
        description="Duración en meses (solo para premium)"
    )
    precio: Optional[float] = Field(None, ge=0, description="Precio del plan")
    metodo_pago: Optional[str] = Field(None, description="Método de pago")
    transaction_id: Optional[str] = Field(None, description="ID de transacción")
    auto_renovacion: bool = Field(default=False, description="Auto-renovación")
    notas: Optional[str] = Field(None, description="Notas adicionales")
    
    @field_validator("plan")
    @classmethod
    def validate_plan_field(cls, v: str) -> str:
        is_valid, error_msg = validate_plan(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("duracion_meses")
    @classmethod
    def validate_duracion_field(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        is_valid, error_msg = validate_duracion(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UpdateSuscripcionRequest(BaseModel):
    """Request para actualizar una suscripción."""
    
    status: Optional[str] = Field(None, description="Nuevo estado")
    end_date: Optional[datetime] = Field(None, description="Nueva fecha de fin")
    auto_renovacion: Optional[bool] = Field(None, description="Auto-renovación")
    notas: Optional[str] = Field(None, description="Nuevas notas")
    
    @field_validator("status")
    @classmethod
    def validate_status_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        is_valid, error_msg = validate_status(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UpgradeToPremiumRequest(BaseModel):
    """Request para upgrade a premium."""
    
    duracion_meses: int = Field(..., ge=1, le=24, description="Duración en meses")
    precio: float = Field(..., gt=0, description="Precio del plan")
    metodo_pago: str = Field(..., description="Método de pago")
    transaction_id: str = Field(..., description="ID de transacción")
    auto_renovacion: bool = Field(default=False, description="Auto-renovación")
    
    @field_validator("duracion_meses")
    @classmethod
    def validate_duracion_field(cls, v: int) -> int:
        is_valid, error_msg = validate_duracion(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("metodo_pago")
    @classmethod
    def validate_metodo_pago_field(cls, v: str) -> str:
        is_valid, error_msg = validate_metodo_pago(v, PlanType.PREMIUM)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower()


class CancelSuscripcionRequest(BaseModel):
    """Request para cancelar suscripción."""
    
    razon: Optional[str] = Field(None, description="Razón de cancelación")


class RenewSuscripcionRequest(BaseModel):
    """Request para renovar suscripción premium."""
    
    duracion_meses: int = Field(..., ge=1, le=24, description="Duración en meses")
    precio: float = Field(..., gt=0, description="Precio del plan")
    transaction_id: str = Field(..., description="ID de transacción")
    
    @field_validator("duracion_meses")
    @classmethod
    def validate_duracion_field(cls, v: int) -> int:
        is_valid, error_msg = validate_duracion(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class SuscripcionFilterParams(FilterParams):
    """Parámetros de filtrado para suscripciones."""
    
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario (INTEGER)")
    plan: Optional[str] = Field(None, description="Filtrar por plan")
    status: Optional[str] = Field(None, description="Filtrar por estado")
    activas_only: bool = Field(default=False, description="Solo suscripciones activas")
    
    # Ordenamiento
    order_by: Literal["id", "created_at", "start_date", "end_date"] = Field(
        default="created_at",
        description="Campo para ordenar"
    )
    order_direction: Literal["asc", "desc"] = Field(
        default="desc",
        description="Dirección del ordenamiento"
    )
    
    # Hereda de FilterParams:
    # - search: Optional[str]
    # - created_after: Optional[datetime]
    # - created_before: Optional[datetime]
    
    @field_validator("plan")
    @classmethod
    def validate_plan_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        is_valid, error_msg = validate_plan(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        is_valid, error_msg = validate_status(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


# ==================== RESPONSE SCHEMAS ====================

class SuscripcionResponse(BaseModel):
    """Response con información completa de una suscripción."""
    
    id: int
    usuario_id: int  # INTEGER
    plan: str
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    precio: Optional[float]
    metodo_pago: Optional[str]
    transaction_id: Optional[str]
    auto_renovacion: bool
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    
    # Propiedades computadas
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    is_freemium: Optional[bool] = None
    dias_restantes: Optional[int] = None
    
    class Config:
        from_attributes = True


class SuscripcionStatsResponse(BaseModel):
    """Response con estadísticas de suscripciones."""
    
    total_suscripciones: int
    suscripciones_activas: int
    suscripciones_freemium: int
    suscripciones_premium: int
    ingresos_totales: float
    tasa_conversion: float  # % de freemium que pasaron a premium
