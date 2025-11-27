"""
Eventos del módulo de notificaciones.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

from src.shared.event_bus import Event


@dataclass
class NotificacionCreadaEvent(Event):
    """Evento emitido cuando se crea una notificación."""
    notificacion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    tipo: str = field(kw_only=True)
    canal: str = field(kw_only=True)
    titulo: str = field(kw_only=True)


@dataclass
class NotificacionEnviadaEvent(Event):
    """Evento emitido cuando se envía una notificación."""
    notificacion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    canal: str = field(kw_only=True)
    enviada_en: datetime = field(kw_only=True)


@dataclass
class NotificacionLeidaEvent(Event):
    """Evento emitido cuando un usuario lee una notificación."""
    notificacion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    leida_en: datetime = field(kw_only=True)


@dataclass
class NotificacionFallidaEvent(Event):
    """Evento emitido cuando falla el envío de una notificación."""
    notificacion_id: int = field(kw_only=True)
    usuario_id: int = field(kw_only=True)
    canal: str = field(kw_only=True)
    error: str = field(kw_only=True)
    intentos: int = field(kw_only=True)


@dataclass
class PreferenciasActualizadasEvent(Event):
    """Evento emitido cuando un usuario actualiza sus preferencias."""
    usuario_id: int = field(kw_only=True)
    preferencias: Dict[str, Any] = field(kw_only=True)


@dataclass
class NotificacionMasivaEvent(Event):
    """Evento emitido cuando se envía una notificación masiva."""
    titulo: str = field(kw_only=True)
    total_usuarios: int = field(kw_only=True)
    canal: str = field(kw_only=True)
    tipo: str = field(kw_only=True)
