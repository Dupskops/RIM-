"""
Eventos del dominio de suscripciones (v2.3 Freemium).

Eventos simplificados para el sistema Freemium:
- Creación de suscripción (automática al registrarse)
- Cambio de plan (Free ↔ Pro o cualquier otro)
- Cancelación de suscripción
"""
from dataclasses import dataclass, field
from typing import Optional

from src.shared.event_bus import Event


# ==================== EVENT CLASSES ====================

@dataclass
class SuscripcionCreatedEvent(Event):
    """Evento: Suscripción creada (automáticamente al registrar usuario)."""
    
    suscripcion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    plan_nombre: str = field(kw_only=True)
    plan_id: int = field(kw_only=True)


@dataclass
class PlanChangedEvent(Event):
    """Evento: Plan cambiado (genérico para upgrade, downgrade, o cualquier cambio)."""
    
    suscripcion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    plan_anterior_id: int = field(kw_only=True)
    plan_anterior_nombre: str = field(kw_only=True)
    plan_nuevo_id: int = field(kw_only=True)
    plan_nuevo_nombre: str = field(kw_only=True)
    changed_by: int = field(kw_only=True)  # ID del usuario que realizó el cambio


@dataclass
class SuscripcionCancelledEvent(Event):
    """Evento: Suscripción cancelada."""
    
    suscripcion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    plan_nombre: str = field(kw_only=True)
    cancelled_by: int = field(kw_only=True)  # ID del usuario que canceló
    razon: Optional[str] = None


# ==================== EMIT HELPER FUNCTIONS ====================

async def emit_suscripcion_created(
    suscripcion_id: int,
    usuario_id: int,
    plan_nombre: str,
    plan_id: int,
) -> None:
    """Emite evento de suscripción creada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan_nombre: Nombre del plan (ej: "FREE", "Pro")
        plan_id: ID del plan
    """
    event = SuscripcionCreatedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan_nombre=plan_nombre,
        plan_id=plan_id,
    )
    await event.emit()


async def emit_plan_changed(
    suscripcion_id: int,
    usuario_id: int,
    plan_anterior_id: int,
    plan_anterior_nombre: str,
    plan_nuevo_id: int,
    plan_nuevo_nombre: str,
    changed_by: int,
) -> None:
    """Emite evento de cambio de plan.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan_anterior_id: ID del plan anterior
        plan_anterior_nombre: Nombre del plan anterior
        plan_nuevo_id: ID del plan nuevo
        plan_nuevo_nombre: Nombre del plan nuevo
        changed_by: ID del usuario que realizó el cambio
    """
    event = PlanChangedEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan_anterior_id=plan_anterior_id,
        plan_anterior_nombre=plan_anterior_nombre,
        plan_nuevo_id=plan_nuevo_id,
        plan_nuevo_nombre=plan_nuevo_nombre,
        changed_by=changed_by,
    )
    await event.emit()


async def emit_suscripcion_cancelled(
    suscripcion_id: int,
    usuario_id: int,
    plan_nombre: str,
    cancelled_by: int,
    razon: Optional[str] = None,
) -> None:
    """Emite evento de suscripción cancelada.
    
    Args:
        suscripcion_id: ID de la suscripción
        usuario_id: ID del usuario
        plan_nombre: Nombre del plan
        cancelled_by: ID del usuario que canceló
        razon: Razón de cancelación (opcional)
    """
    event = SuscripcionCancelledEvent(
        suscripcion_id=suscripcion_id,
        usuario_id=usuario_id,
        plan_nombre=plan_nombre,
        cancelled_by=cancelled_by,
        razon=razon,
    )
    await event.emit()


__all__ = [
    "SuscripcionCreatedEvent",
    "PlanChangedEvent",
    "SuscripcionCancelledEvent",
    "emit_suscripcion_created",
    "emit_plan_changed",
    "emit_suscripcion_cancelled",
]

