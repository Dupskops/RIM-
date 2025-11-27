"""
Esquemas Pydantic para validación de datos del chatbot.

Alineado con MVP v2.3 - Sistema de límites Freemium.
Elimina campos obsoletos (nivel_acceso, tokens, feedback, etc.)
"""
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from ..shared.base_models import FilterParams


# ============================================
# FILTROS
# ============================================

class ConversacionFilterParams(FilterParams):
    """Parámetros de filtrado para conversaciones."""
    
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario")
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    solo_activas: Optional[bool] = Field(None, description="Solo conversaciones activas")
    fecha_desde: Optional[date] = Field(None, description="Fecha de creación desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de creación hasta")


# ============================================
# REQUEST SCHEMAS
# ============================================

class ConversacionCreate(BaseModel):
    """Esquema para crear una conversación."""
    moto_id: int = Field(..., gt=0, description="ID de la moto (obligatorio en v2.3)")
    titulo: Optional[str] = Field(None, min_length=1, max_length=200, description="Título opcional (se genera automáticamente)")


class MensajeCreate(BaseModel):
    """Esquema para crear un mensaje."""
    contenido: str = Field(..., min_length=1, max_length=2000, description="Contenido del mensaje")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt: diagnostic/maintenance/explanation/general")


class ChatRequest(BaseModel):
    """Esquema para solicitud de chat (streaming o no)."""
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(None, description="ID de conversación existente")
    moto_id: int = Field(..., gt=0, description="ID de moto (obligatorio)")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt (se detecta automáticamente si no se provee)")
    stream: bool = Field(False, description="Si se requiere streaming")
    context: Optional[dict] = Field(None, description="Contexto adicional (sensores, fallas, etc.)")


class LimiteCheckRequest(BaseModel):
    """Esquema para verificar límites de chatbot."""
    usuario_id: int = Field(..., gt=0, description="ID del usuario")


# ============================================
# RESPONSE SCHEMAS
# ============================================

class MensajeResponse(BaseModel):
    """Esquema de respuesta de mensaje (MVP v2.3)."""
    id: int
    conversacion_id: int
    role: str  # "user" o "assistant"
    contenido: str
    tipo_prompt: Optional[str]  # "diagnostic", "maintenance", "explanation", "general"
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversacionResponse(BaseModel):
    """Esquema de respuesta de conversación (MVP v2.3)."""
    id: int
    conversation_id: str
    usuario_id: int
    moto_id: int  # Ahora es obligatorio
    titulo: Optional[str]
    activa: bool
    total_mensajes: int
    ultima_actividad: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversacionWithMessagesResponse(BaseModel):
    """Esquema de conversación con sus mensajes."""
    conversacion: ConversacionResponse
    mensajes: List[MensajeResponse]


class ConversacionStatsResponse(BaseModel):
    """Esquema de estadísticas de conversaciones (MVP v2.3)."""
    total_conversaciones: int
    conversaciones_activas: int
    conversaciones_archivadas: int


class ChatResponse(BaseModel):
    """Esquema de respuesta de chat (MVP v2.3)."""
    message: str = Field(..., description="Respuesta del asistente")
    conversation_id: str = Field(..., description="ID de la conversación")
    mensaje_usuario_id: int = Field(..., description="ID del mensaje del usuario")
    mensaje_asistente_id: int = Field(..., description="ID del mensaje del asistente")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt usado")


class ChatStreamChunk(BaseModel):
    """Esquema para chunks de streaming."""
    chunk: str = Field(..., description="Fragmento de texto")
    done: bool = Field(False, description="Si es el último chunk")


class LimiteCheckResponse(BaseModel):
    """Esquema de respuesta de verificación de límites."""
    puede_crear: bool = Field(..., description="Si el usuario puede crear una nueva conversación")
    usos_realizados: int = Field(..., description="Conversaciones creadas este mes")
    limite_mensual: Optional[int] = Field(None, description="Límite mensual (None si es Pro)")
    usos_restantes: Optional[int] = Field(None, description="Conversaciones restantes (None si es Pro)")
    es_pro: bool = Field(..., description="Si el usuario tiene plan Pro")
    periodo_mes: date = Field(..., description="Período actual (primer día del mes)")


# ============================================
# WEBSOCKET SCHEMAS (MVP v2.3)
# ============================================

class WSChatMessage(BaseModel):
    """Esquema de mensaje de chat por WebSocket."""
    type: str = "chat_message"
    message: str = Field(..., min_length=1, max_length=2000)
    moto_id: int = Field(..., gt=0, description="ID de la moto (obligatorio)")
    conversation_id: Optional[str] = Field(None, description="ID de conversación existente")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt (opcional)")
    context: Optional[dict] = Field(None, description="Contexto adicional")


class WSTypingIndicator(BaseModel):
    """Esquema para indicador de escritura."""
    type: str  # "typing_start" o "typing_stop"
    conversation_id: Optional[str] = None


class WSHistoryRequest(BaseModel):
    """Esquema para solicitar historial."""
    type: str = "get_history"
    conversation_id: str = Field(..., description="ID de la conversación")
    limit: Optional[int] = Field(50, ge=1, le=200)


class WSChatResponse(BaseModel):
    """Esquema de respuesta de chat por WebSocket (MVP v2.3)."""
    type: str = "chat_response"
    content: str
    role: str = "assistant"
    conversation_id: str
    mensaje_id: int
    tipo_prompt: Optional[str] = None
    timestamp: str


class WSStreamChunk(BaseModel):
    """Esquema para streaming por WebSocket."""
    type: str = "stream_chunk"
    content: str
    done: bool = False


class WSStreamComplete(BaseModel):
    """Esquema para indicar fin de streaming."""
    type: str = "stream_complete"
    conversation_id: str
    mensaje_id: int
    total_length: int


class WSError(BaseModel):
    """Esquema para errores por WebSocket."""
    type: str = "error"
    message: str
    code: Optional[str] = None


class WSHistoryResponse(BaseModel):
    """Esquema para respuesta de historial."""
    type: str = "history"
    conversation_id: str
    messages: List[MensajeResponse]
    total: int


class WSLimiteAlcanzado(BaseModel):
    """Esquema para notificar límite alcanzado."""
    type: str = "limite_alcanzado"
    mensaje: str
    usos_realizados: int
    limite_mensual: int
    es_pro: bool
