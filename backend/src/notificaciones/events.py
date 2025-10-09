"""
Eventos del módulo de notificaciones.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.shared.event_bus import Event


@dataclass
class NotificacionCreadaEvent(Event):
    """Evento emitido cuando se crea una notificación."""
    notificacion_id: int
    usuario_id: int
    tipo: str
    canal: str
    titulo: str


@dataclass
class NotificacionEnviadaEvent(Event):
    """Evento emitido cuando se envía una notificación."""
    notificacion_id: int
    usuario_id: int
    canal: str
    enviada_en: datetime


@dataclass
class NotificacionLeidaEvent(Event):
    """Evento emitido cuando un usuario lee una notificación."""
    notificacion_id: int
    usuario_id: int
    leida_en: datetime


@dataclass
class NotificacionFallidaEvent(Event):
    """Evento emitido cuando falla el envío de una notificación."""
    notificacion_id: int
    usuario_id: int
    canal: str
    error: str
    intentos: int


@dataclass
class PreferenciasActualizadasEvent(Event):
    """Evento emitido cuando un usuario actualiza sus preferencias."""
    usuario_id: int
    preferencias: dict


@dataclass
class NotificacionMasivaEvent(Event):
    """Evento emitido cuando se envía una notificación masiva."""
    titulo: str
    total_usuarios: int
    canal: str
    tipo: str
