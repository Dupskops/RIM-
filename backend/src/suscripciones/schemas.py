"""
Schemas Pydantic para suscripciones (DTOs).

Estos esquemas se basan en `docs/SCHEMAS.md` (sección suscripciones).
Incluyen: request/response para checkout, notificaciones de pago, transacciones
y objetos relacionados a la suscripción de usuario.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, List
from enum import Enum

from pydantic import BaseModel, Field


# ----------------------
# Enums
# ----------------------


class CancelMode(str, Enum):
    """Modos de cancelación de suscripción."""
    IMMEDIATE = "immediate"
    END_OF_PERIOD = "end_of_period"


# ----------------------
# Sub-esquemas básicos
# ----------------------


class CaracteristicaReadSchema(BaseModel):
    clave_funcion: str
    descripcion: str


class PlanReadSchema(BaseModel):
    id: int
    nombre_plan: str
    precio: Decimal = Field(..., description="Precio en Decimal — serializar como string/number con cuidado")
    periodo_facturacion: str
    caracteristicas: List[CaracteristicaReadSchema] = []


# ----------------------
# Suscripción (usuario)
# ----------------------


class SuscripcionUsuarioReadSchema(BaseModel):
    suscripcion_id: int
    plan: PlanReadSchema
    estado_suscripcion: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None

    class Config:
        from_attributes = True


# ----------------------
# Transacciones / Pagos
# ----------------------


class TransaccionCreateResponse(BaseModel):
    transaccion_id: int
    payment_token: str = Field(
        ...,
        description=(
            "Token/valor que el cliente usará para completar o simular el pago. "
            "Convención MVP: '0' => success, '1' => failed"
        ),
    )


class TransaccionReadSchema(BaseModel):
    transaccion_id: int
    usuario_id: Optional[int] = None
    plan_id: Optional[int] = None
    monto: Decimal
    status: str  # pending | success | failed
    provider_metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaymentNotificationSchema(BaseModel):
    transaccion_id: int
    payment_token: str
    metadata: Optional[dict[str, Any]] = None


# ----------------------
# Requests para Checkout / Cancel / Admin
# ----------------------


class CheckoutCreateRequest(BaseModel):
    usuario_id: int
    plan_id: int
    monto: Optional[Decimal] = None
    payment_method: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class SuscripcionCancelRequest(BaseModel):
    mode: CancelMode = Field(
        ..., 
        description="Modo de cancelación: 'immediate' (inmediato) o 'end_of_period' (al final del periodo)"
    )
    reason: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Motivo opcional de cancelación"
    )


class AdminAssignSubscriptionRequest(BaseModel):
    usuario_id: int
    plan_id: int
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None


__all__ = [
    "CancelMode",
    "CaracteristicaReadSchema",
    "PlanReadSchema",
    "SuscripcionUsuarioReadSchema",
    "TransaccionCreateResponse",
    "TransaccionReadSchema",
    "PaymentNotificationSchema",
    "CheckoutCreateRequest",
    "SuscripcionCancelRequest",
    "AdminAssignSubscriptionRequest",
]
