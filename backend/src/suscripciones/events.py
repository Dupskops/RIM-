"""
Eventos del dominio de suscripciones.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from src.shared.event_bus import Event


# ==================== EVENT CLASSES ====================

@dataclass
class SuscripcionCreatedEvent(Event):
    """Evento: Suscripción creada."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    plan: str = field(default="")
    precio: Optional[float] = None


@dataclass
class SuscripcionUpgradedEvent(Event):
    """Evento: Upgrade a premium."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    old_plan: str = field(default="")
    new_plan: str = field(default="")
    precio: float = field(default=0.0)
    duracion_meses: int = field(default=0)


@dataclass
class SuscripcionCancelledEvent(Event):
    """Evento: Suscripción cancelada."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    plan: str = field(default="")
    cancelled_by: str = field(default="")  # UUID
    razon: Optional[str] = None


@dataclass
class SuscripcionRenewedEvent(Event):
    """Evento: Suscripción renovada."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    plan: str = field(default="")
    new_end_date: datetime = field(default_factory=datetime.utcnow)
    precio: float = field(default=0.0)


@dataclass
class SuscripcionExpiredEvent(Event):
    """Evento: Suscripción expirada."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    plan: str = field(default="")
    expired_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SuscripcionUpdatedEvent(Event):
    """Evento: Suscripción actualizada."""
    
    suscripcion_id: int = field(default=0)
    usuario_id: str = field(default="")  # UUID
    updated_fields: list[str] = field(default_factory=list)
    updated_by: str = field(default="")  # UUID


# ==================== EMIT HELPER FUNCTIONS ====================

async def emit_suscripcion_created(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    plan: str,
    precio: Optional[float] = None
) -> None:
    """
    Emite evento de suscripción creada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan: Tipo de plan
        precio: Precio (opcional)
    """
    event = SuscripcionCreatedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan=plan,
        precio=precio
    )
    await event.emit()


async def emit_suscripcion_upgraded(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    old_plan: str,
    new_plan: str,
    precio: float,
    duracion_meses: int
) -> None:
    """
    Emite evento de upgrade a premium.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        old_plan: Plan anterior
        new_plan: Plan nuevo
        precio: Precio pagado
        duracion_meses: Duración en meses
    """
    event = SuscripcionUpgradedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        old_plan=old_plan,
        new_plan=new_plan,
        precio=precio,
        duracion_meses=duracion_meses
    )
    await event.emit()


async def emit_suscripcion_cancelled(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    plan: str,
    cancelled_by: str,  # UUID
    razon: Optional[str] = None
) -> None:
    """
    Emite evento de suscripción cancelada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan: Tipo de plan
        cancelled_by: ID del usuario que canceló
        razon: Razón de cancelación (opcional)
    """
    event = SuscripcionCancelledEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan=plan,
        razon=razon,
        cancelled_by=cancelled_by
    )
    await event.emit()


async def emit_suscripcion_renewed(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    plan: str,
    new_end_date: datetime,
    precio: float
) -> None:
    """
    Emite evento de suscripción renovada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan: Tipo de plan
        new_end_date: Nueva fecha de fin
        precio: Precio pagado
    """
    event = SuscripcionRenewedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan=plan,
        new_end_date=new_end_date,
        precio=precio
    )
    await event.emit()


async def emit_suscripcion_expired(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    plan: str,
    expired_at: datetime
) -> None:
    """
    Emite evento de suscripción expirada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan: Tipo de plan
        expired_at: Fecha de expiración
    """
    event = SuscripcionExpiredEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan=plan,
        expired_at=expired_at
    )
    await event.emit()


async def emit_suscripcion_updated(
    suscripcion_id: int,
    usuario_id: str,  # UUID
    updated_fields: list[str],
    updated_by: str  # UUID
) -> None:
    """
    Emite evento de suscripción actualizada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        updated_fields: Campos actualizados
        updated_by: ID del usuario que actualizó
    """
    event = SuscripcionUpdatedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        updated_fields=updated_fields,
        updated_by=updated_by
    )
    await event.emit()
