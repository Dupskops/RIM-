"""
Eventos del módulo de usuarios.
Define los eventos emitidos por el sistema de gestión de usuarios.
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from src.shared.event_bus import Event, event_bus


# ============================================
# CLASES DE EVENTOS
# ============================================

@dataclass
class UsuarioCreatedEvent(Event):
    """Evento emitido cuando un admin crea un usuario."""
    usuario_id: str = ""
    email: str = ""
    nombre: str = ""
    created_by_admin_id: str = ""


@dataclass
class UsuarioUpdatedEvent(Event):
    """Evento emitido cuando un admin actualiza un usuario."""
    usuario_id: str = ""
    email: str = ""
    updated_by_admin_id: str = ""
    changes: dict = None  # type: ignore


@dataclass
class UsuarioDeletedEvent(Event):
    """Evento emitido cuando un admin elimina un usuario."""
    usuario_id: str = ""
    email: str = ""
    deleted_by_admin_id: str = ""


@dataclass
class UsuarioDeactivatedEvent(Event):
    """Evento emitido cuando un admin desactiva un usuario."""
    usuario_id: str = ""
    email: str = ""
    deactivated_by_admin_id: str = ""


@dataclass
class UsuarioActivatedEvent(Event):
    """Evento emitido cuando un admin activa un usuario."""
    usuario_id: int = 0
    email: str = ""
    activated_by_admin_id: int = 0


# ============================================
# MÉTODOS HELPER PARA EMITIR EVENTOS
# ============================================

async def emit_usuario_created(
    usuario_id: str,
    email: str,
    nombre: str,
    created_by_admin_id: str
) -> None:
    """
    Emite evento de usuario creado por admin.
    
    Args:
        usuario_id: ID del usuario creado
        email: Email del usuario
        nombre: Nombre del usuario
        created_by_admin_id: ID del admin que creó el usuario
    """
    await event_bus.publish(UsuarioCreatedEvent(
        usuario_id=usuario_id,
        email=email,
        nombre=nombre,
        created_by_admin_id=created_by_admin_id,
    ))


async def emit_usuario_updated(
    usuario_id: str,
    email: str,
    updated_by_admin_id: str,
    changes: dict
) -> None:
    """
    Emite evento de usuario actualizado por admin.
    
    Args:
        usuario_id: ID del usuario actualizado
        email: Email del usuario
        updated_by_admin_id: ID del admin que actualizó
        changes: Diccionario con campos modificados
    """
    await event_bus.publish(UsuarioUpdatedEvent(
        usuario_id=usuario_id,
        email=email,
        updated_by_admin_id=updated_by_admin_id,
        changes=changes,
    ))


async def emit_usuario_deleted(
    usuario_id: str,
    email: str,
    deleted_by_admin_id: str
) -> None:
    """
    Emite evento de usuario eliminado por admin.
    
    Args:
        usuario_id: ID del usuario eliminado
        email: Email del usuario
        deleted_by_admin_id: ID del admin que eliminó
    """
    await event_bus.publish(UsuarioDeletedEvent(
        usuario_id=usuario_id,
        email=email,
        deleted_by_admin_id=deleted_by_admin_id,
    ))


async def emit_usuario_deactivated(
    usuario_id: str,
    email: str,
    deactivated_by_admin_id: str
) -> None:
    """
    Emite evento de usuario desactivado por admin.
    
    Args:
        usuario_id: ID del usuario desactivado
        email: Email del usuario
        deactivated_by_admin_id: ID del admin que desactivó
    """
    await event_bus.publish(UsuarioDeactivatedEvent(
        usuario_id=usuario_id,
        email=email,
        deactivated_by_admin_id=deactivated_by_admin_id,
    ))


async def emit_usuario_activated(
    usuario_id: int,
    email: str,
    activated_by_admin_id: int
) -> None:
    """
    Emite evento de usuario activado por admin.
    
    Args:
        usuario_id: ID del usuario activado
        email: Email del usuario
        activated_by_admin_id: ID del admin que activó
    """
    await event_bus.publish(UsuarioActivatedEvent(
        usuario_id=usuario_id,
        email=email,
        activated_by_admin_id=activated_by_admin_id,
    ))
