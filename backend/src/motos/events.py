"""
Eventos del dominio de motos.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from src.shared.event_bus import Event


# ==================== EVENT CLASSES ====================

@dataclass
class MotoRegisteredEvent(Event):
    """Evento: Moto registrada."""
    
    moto_id: int
    usuario_id: int
    vin: str
    modelo: str
    año: int
    placa: Optional[str]
    timestamp: Optional[datetime] = None  # Agregado explícitamente para evitar errores de dataclass


@dataclass
class MotoUpdatedEvent(Event):
    """Evento: Moto actualizada."""
    
    moto_id: int
    usuario_id: int
    updated_fields: list[str]
    updated_by: int
    timestamp: Optional[datetime] = None


@dataclass
class MotoDeletedEvent(Event):
    """Evento: Moto eliminada."""
    
    moto_id: int
    usuario_id: int
    vin: str
    deleted_by: int
    timestamp: Optional[datetime] = None


@dataclass
class KilometrajeUpdatedEvent(Event):
    """Evento: Kilometraje actualizado."""
    
    moto_id: int
    usuario_id: int
    old_kilometraje: int
    new_kilometraje: int
    updated_by: int
    timestamp: Optional[datetime] = None


@dataclass
class MotoTransferredEvent(Event):
    """Evento: Moto transferida a otro usuario."""
    
    moto_id: int
    old_usuario_id: int
    new_usuario_id: int
    transferred_by: int
    timestamp: Optional[datetime] = None


# ==================== EMIT HELPER FUNCTIONS ====================

async def emit_moto_registered(
    moto_id: int,
    usuario_id: int,
    vin: str,
    modelo: str,
    año: int,
    placa: Optional[str] = None
) -> None:
    """
    Emite evento de moto registrada.
    
    Args:
        moto_id: ID de la moto
        usuario_id: ID del usuario propietario
        vin: VIN de la moto
        modelo: Modelo de la moto
        año: Año de fabricación
        placa: Placa (opcional)
    """
    event = MotoRegisteredEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        usuario_id=usuario_id,
        vin=vin,
        modelo=modelo,
        año=año,
        placa=placa
    )
    await event.emit()


async def emit_moto_updated(
    moto_id: int,
    usuario_id: int,
    updated_fields: list[str],
    updated_by: int
) -> None:
    """
    Emite evento de moto actualizada.
    
    Args:
        moto_id: ID de la moto
        usuario_id: ID del usuario propietario
        updated_fields: Lista de campos actualizados
        updated_by: ID del usuario que realizó la actualización
    """
    event = MotoUpdatedEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        usuario_id=usuario_id,
        updated_fields=updated_fields,
        updated_by=updated_by
    )
    await event.emit()


async def emit_moto_deleted(
    moto_id: int,
    usuario_id: int,
    vin: str,
    deleted_by: int
) -> None:
    """
    Emite evento de moto eliminada.
    
    Args:
        moto_id: ID de la moto
        usuario_id: ID del usuario propietario
        vin: VIN de la moto
        deleted_by: ID del usuario que realizó la eliminación
    """
    event = MotoDeletedEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        usuario_id=usuario_id,
        vin=vin,
        deleted_by=deleted_by
    )
    await event.emit()


async def emit_kilometraje_updated(
    moto_id: int,
    usuario_id: int,
    old_kilometraje: int,
    new_kilometraje: int,
    updated_by: int
) -> None:
    """
    Emite evento de kilometraje actualizado.
    
    Args:
        moto_id: ID de la moto
        usuario_id: ID del usuario propietario
        old_kilometraje: Kilometraje anterior
        new_kilometraje: Nuevo kilometraje
        updated_by: ID del usuario que realizó la actualización
    """
    event = KilometrajeUpdatedEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        usuario_id=usuario_id,
        old_kilometraje=old_kilometraje,
        new_kilometraje=new_kilometraje,
        updated_by=updated_by
    )
    await event.emit()


async def emit_moto_transferred(
    moto_id: int,
    old_usuario_id: int,
    new_usuario_id: int,
    transferred_by: int
) -> None:
    """
    Emite evento de moto transferida.
    
    Args:
        moto_id: ID de la moto
        old_usuario_id: ID del antiguo propietario
        new_usuario_id: ID del nuevo propietario
        transferred_by: ID del usuario que realizó la transferencia
    """
    event = MotoTransferredEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        old_usuario_id=old_usuario_id,
        new_usuario_id=new_usuario_id,
        transferred_by=transferred_by
    )
    await event.emit()
