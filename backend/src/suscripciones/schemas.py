"""
Schemas Pydantic para suscripciones (DTOs).

Estos esquemas se basan en `docs/SCHEMAS.md` (sección suscripciones).
Incluyen: request/response para checkout, notificaciones de pago, transacciones
y objetos relacionados a la suscripción de usuario.
"""
from __future__ import annotations

from datetime import datetime, date
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
    """Schema para lectura de características (v2.3)."""
    id: Optional[int] = None
    clave_funcion: str
    descripcion: Optional[str] = None
    limite_free: Optional[int] = Field(
        None,
        description="Límite mensual para plan Free. NULL=ilimitado, 0=bloqueado, >0=límite"
    )
    limite_pro: Optional[int] = Field(
        None,
        description="Límite mensual para plan Pro. NULL=ilimitado, 0=bloqueado, >0=límite"
    )

    class Config:
        from_attributes = True


class PlanReadSchema(BaseModel):
    id: int
    nombre_plan: str
    precio: Decimal = Field(..., description="Precio en Decimal — serializar como string/number con cuidado")
    periodo_facturacion: Optional[str] = None
    caracteristicas: List[CaracteristicaReadSchema] = []

    class Config:
        from_attributes = True


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


# ----------------------
# Schemas v2.3 Freemium (Límites)
# ----------------------


class SuscripcionReadSchema(BaseModel):
    """Schema para lectura de suscripción (v2.3)."""
    id: int
    usuario_id: int
    plan: Optional[PlanReadSchema] = None
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado_suscripcion: Optional[str] = None

    class Config:
        from_attributes = True


class LimiteCheckResponse(BaseModel):
    """Respuesta al verificar límite de una característica."""
    puede_usar: bool = Field(..., description="True si puede usar la característica")
    usos_realizados: int = Field(..., description="Número de usos realizados este mes")
    limite: Optional[int] = Field(None, description="Límite mensual (NULL=ilimitado)")
    usos_restantes: Optional[int] = Field(None, description="Usos restantes este mes")
    mensaje: str = Field(..., description="Mensaje descriptivo del estado")
    periodo_actual: date = Field(..., description="Primer día del mes actual (solo fecha)")


class LimiteRegistroResponse(BaseModel):
    """Respuesta al registrar un uso de característica."""
    exito: bool = Field(..., description="True si se registró exitosamente")
    usos_realizados: int = Field(..., description="Número total de usos después del registro")
    limite: Optional[int] = Field(None, description="Límite mensual")
    usos_restantes: Optional[int] = Field(None, description="Usos restantes")
    mensaje: str = Field(..., description="Mensaje descriptivo")


class UsoHistorialResponse(BaseModel):
    """Respuesta con historial de uso de una característica."""
    caracteristica: str = Field(..., description="Clave de la característica")
    usos_realizados: int = Field(..., description="Usos realizados este mes")
    limite_mensual: int = Field(..., description="Límite mensual copiado")
    ultimo_uso_at: Optional[datetime] = Field(None, description="Timestamp del último uso")
    periodo_mes: date = Field(..., description="Primer día del mes (solo fecha)")

    class Config:
        from_attributes = True


class CambiarPlanRequest(BaseModel):
    """Request para cambiar de plan (genérico)."""
    plan_id: int = Field(..., description="ID del plan destino", gt=0)


__all__ = [
    "CancelMode",
    "CaracteristicaReadSchema",
    "PlanReadSchema",
    "SuscripcionUsuarioReadSchema",
    "SuscripcionReadSchema",
    "TransaccionCreateResponse",
    "TransaccionReadSchema",
    "PaymentNotificationSchema",
    "CheckoutCreateRequest",
    "SuscripcionCancelRequest",
    "AdminAssignSubscriptionRequest",
    "LimiteCheckResponse",
    "LimiteRegistroResponse",
    "UsoHistorialResponse",
    "CambiarPlanRequest",
]
