"""
Eventos del módulo de autenticación.
Define los eventos emitidos por el sistema de auth.
"""
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from src.shared.event_bus import Event, event_bus


# ============================================
# CLASES DE EVENTOS
# ============================================

@dataclass
class UserRegisteredEvent(Event):
    """Evento emitido cuando un usuario se registra."""
    user_id: str = ""
    email: str = ""
    nombre: str = ""
    verification_token: Optional[str] = None


@dataclass
class UserLoggedInEvent(Event):
    """Evento emitido cuando un usuario inicia sesión."""
    user_id: str = ""
    email: str = ""
    ip_address: Optional[str] = None


@dataclass
class PasswordChangedEvent(Event):
    """Evento emitido cuando un usuario cambia su contraseña."""
    user_id: str = ""
    email: str = ""


@dataclass
class PasswordResetRequestedEvent(Event):
    """Evento emitido cuando se solicita un reset de contraseña."""
    user_id: str = ""
    email: str = ""
    reset_token: str = ""


@dataclass
class PasswordResetCompletedEvent(Event):
    """Evento emitido cuando se completa un reset de contraseña."""
    user_id: str = ""


@dataclass
class EmailVerifiedEvent(Event):
    """Evento emitido cuando se verifica un email."""
    user_id: str = ""


@dataclass
class UserDeactivatedEvent(Event):
    """Evento emitido cuando se desactiva un usuario."""
    user_id: str = ""
    email: str = ""
    reason: Optional[str] = None


@dataclass
class SessionRevokedEvent(Event):
    """Evento emitido cuando se revoca una sesión."""
    user_id: str = ""
    email: str = ""
    reason: Optional[str] = None


# ============================================
# MÉTODOS HELPER PARA EMITIR EVENTOS
# ============================================

async def emit_user_registered(
    user_id: str,
    email: str,
    nombre: str,
    verification_token: Optional[str] = None
) -> None:
    """
    Emite evento de usuario registrado.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        nombre: Nombre del usuario
        verification_token: Token de verificación (opcional)
    """
    await event_bus.publish(UserRegisteredEvent(
        user_id=user_id,
        email=email,
        nombre=nombre,
        verification_token=verification_token,
    ))


async def emit_user_logged_in(
    user_id: str,
    email: str,
    ip_address: Optional[str] = None
) -> None:
    """
    Emite evento de usuario autenticado.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        ip_address: IP del cliente (opcional)
    """
    await event_bus.publish(UserLoggedInEvent(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
    ))


async def emit_password_changed(
    user_id: str,
    email: str
) -> None:
    """
    Emite evento de contraseña cambiada.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
    """
    await event_bus.publish(PasswordChangedEvent(
        user_id=user_id,
        email=email,
    ))


async def emit_password_reset_requested(
    user_id: str,
    email: str,
    reset_token: str
) -> None:
    """
    Emite evento de reset de contraseña solicitado.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        reset_token: Token de reset
    """
    await event_bus.publish(PasswordResetRequestedEvent(
        user_id=user_id,
        email=email,
        reset_token=reset_token,
    ))


async def emit_password_reset_completed(
    user_id: str
) -> None:
    """
    Emite evento de reset de contraseña completado.
    
    Args:
        user_id: ID del usuario
    """
    await event_bus.publish(PasswordResetCompletedEvent(
        user_id=user_id,
    ))


async def emit_email_verified(
    user_id: str
) -> None:
    """
    Emite evento de email verificado.
    
    Args:
        user_id: ID del usuario
    """
    await event_bus.publish(EmailVerifiedEvent(
        user_id=user_id,
    ))


async def emit_user_deactivated(
    user_id: str,
    email: str,
    reason: Optional[str] = None
) -> None:
    """
    Emite evento de usuario desactivado.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        reason: Razón de desactivación (opcional)
    """
    await event_bus.publish(UserDeactivatedEvent(
        user_id=user_id,
        email=email,
        reason=reason,
    ))


async def emit_session_revoked(
    user_id: str,
    email: str,
    reason: Optional[str] = None
) -> None:
    """
    Emite evento de sesión revocada.
    
    Args:
        user_id: ID del usuario
        email: Email del usuario
        reason: Razón de revocación (opcional)
    """
    await event_bus.publish(SessionRevokedEvent(
        user_id=user_id,
        email=email,
        reason=reason,
    ))

