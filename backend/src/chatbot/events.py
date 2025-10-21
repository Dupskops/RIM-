"""
Eventos del módulo de chatbot.
"""
from dataclasses import dataclass
from typing import Optional

from src.shared.event_bus import Event


@dataclass
class ConversacionIniciadaEvent(Event):
    """Evento emitido cuando se inicia una nueva conversación."""
    conversacion_id: str = ""
    usuario_id: int = 0
    moto_id: Optional[int] = None
    nivel_acceso: str = ""
    titulo: str = ""


@dataclass
class MensajeEnviadoEvent(Event):
    """Evento emitido cuando el usuario envía un mensaje."""
    conversacion_id: str = ""
    usuario_id: int = 0
    contenido: str = ""
    tipo_prompt: str = ""


@dataclass
class RespuestaGeneradaEvent(Event):
    """Evento emitido cuando el chatbot genera una respuesta."""
    conversacion_id: str = ""
    contenido: str = ""
    tokens_usados: int = 0
    tiempo_respuesta_ms: int = 0
    modelo_usado: str = ""
    tipo_prompt: str = ""
    confianza: Optional[float] = None


@dataclass
class FeedbackRecibidoEvent(Event):
    """Evento emitido cuando se recibe feedback de un mensaje."""
    mensaje_id: int = 0
    conversacion_id: str = ""
    usuario_id: int = 0
    util: bool = False
    feedback: str = ""


@dataclass
class ErrorChatbotEvent(Event):
    """Evento emitido cuando ocurre un error en el chatbot."""
    conversacion_id: str = ""
    usuario_id: int = 0
    error_tipo: str = ""
    error_mensaje: str = ""
    contexto: str = ""


@dataclass
class ConversacionFinalizadaEvent(Event):
    """Evento emitido cuando se finaliza/archiva una conversación."""
    conversacion_id: str = ""
    usuario_id: int = 0
    total_mensajes: int = 0
    duracion_minutos: int = 0


@dataclass
class LimiteAlcanzadoEvent(Event):
    """Evento emitido cuando un usuario alcanza límites (Freemium)."""
    usuario_id: int = 0
    limite_tipo: str = ""  # "mensajes_diarios", "tokens_diarios", etc.
    valor_actual: int = 0
    limite_maximo: int = 0
    nivel_acceso: str = ""
