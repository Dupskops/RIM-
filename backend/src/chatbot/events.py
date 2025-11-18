"""
Eventos del módulo de chatbot.

Eventos simplificados alineados con MVP v2.3.
"""
from dataclasses import dataclass

from src.shared.event_bus import Event


@dataclass
class ConversacionIniciadaEvent(Event):
    """Evento emitido cuando se inicia una nueva conversación."""
    conversation_id: str = ""
    usuario_id: int = 0
    moto_id: int = 0


@dataclass
class MensajeEnviadoEvent(Event):
    """Evento emitido cuando el usuario envía un mensaje."""
    conversation_id: str = ""
    usuario_id: int = 0
    contenido: str = ""


@dataclass
class RespuestaGeneradaEvent(Event):
    """Evento emitido cuando el chatbot genera una respuesta."""
    conversation_id: str = ""
    mensaje_id: int = 0
    tipo_prompt: str = ""


@dataclass
class ErrorChatbotEvent(Event):
    """Evento emitido cuando ocurre un error en el chatbot."""
    conversation_id: str = ""
    usuario_id: int = 0
    error_type: str = ""
    error_message: str = ""


@dataclass
class ConversacionFinalizadaEvent(Event):
    """Evento emitido cuando se finaliza/archiva una conversación."""
    conversation_id: str = ""
    usuario_id: int = 0
    total_mensajes: int = 0
