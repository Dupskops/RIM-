"""
Esquemas Pydantic para validación de datos del chatbot.
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
    nivel_acceso: Optional[str] = Field(None, description="Filtrar por nivel (freemium/premium)")
    solo_activas: Optional[bool] = Field(None, description="Solo conversaciones activas")
    fecha_desde: Optional[date] = Field(None, description="Fecha de creación desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de creación hasta")


# ============================================
# REQUEST SCHEMAS
# ============================================

class ConversacionCreate(BaseModel):
    """Esquema para crear una conversación."""
    titulo: str = Field(..., min_length=1, max_length=200, description="Título de la conversación")
    moto_id: Optional[int] = Field(None, gt=0, description="ID de la moto (opcional)")


class MensajeCreate(BaseModel):
    """Esquema para crear un mensaje."""
    contenido: str = Field(..., min_length=1, max_length=10000, description="Contenido del mensaje")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt: diagnostic/maintenance/explanation")


class MensajeFeedback(BaseModel):
    """Esquema para dar feedback a un mensaje."""
    util: bool = Field(..., description="Si la respuesta fue útil")
    feedback: Optional[str] = Field(None, max_length=1000, description="Comentarios adicionales")


class ChatRequest(BaseModel):
    """Esquema para solicitud de chat (streaming o no)."""
    message: str = Field(..., min_length=1, max_length=10000, description="Mensaje del usuario")
    conversation_id: Optional[str] = Field(None, description="ID de conversación existente")
    moto_id: Optional[int] = Field(None, gt=0, description="ID de moto para contexto")
    tipo_prompt: Optional[str] = Field("general", description="Tipo de prompt")
    stream: bool = Field(True, description="Si se requiere streaming")


# ============================================
# RESPONSE SCHEMAS
# ============================================

class MensajeResponse(BaseModel):
    """Esquema de respuesta de mensaje."""
    id: int
    conversacion_id: int
    role: str
    contenido: str
    tokens_usados: Optional[int]
    tiempo_respuesta_ms: Optional[int]
    modelo_usado: Optional[str]
    tipo_prompt: Optional[str]
    confianza: Optional[float]
    util: Optional[bool]
    feedback: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversacionResponse(BaseModel):
    """Esquema de respuesta de conversación."""
    id: int
    conversation_id: str
    usuario_id: int
    moto_id: Optional[int]
    titulo: str
    nivel_acceso: str
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
    """Esquema de estadísticas de conversaciones."""
    total_conversaciones: int
    conversaciones_activas: int
    total_mensajes: int
    promedio_mensajes_por_conversacion: float
    tiempo_respuesta_promedio_ms: float
    tokens_totales_usados: int
    modelo_mas_usado: str
    tipo_prompt_mas_usado: str
    tasa_utilidad: float  # Porcentaje de mensajes marcados como útiles


class ChatResponse(BaseModel):
    """Esquema de respuesta de chat."""
    message: str = Field(..., description="Respuesta del asistente")
    conversation_id: str = Field(..., description="ID de la conversación")
    mensaje_id: int = Field(..., description="ID del mensaje guardado")
    tokens_usados: Optional[int] = Field(None, description="Tokens consumidos")
    tiempo_respuesta_ms: Optional[int] = Field(None, description="Tiempo de respuesta en ms")
    modelo_usado: Optional[str] = Field(None, description="Modelo usado")
    tipo_prompt: Optional[str] = Field(None, description="Tipo de prompt usado")


class ChatStreamChunk(BaseModel):
    """Esquema para chunks de streaming."""
    chunk: str = Field(..., description="Fragmento de texto")
    done: bool = Field(False, description="Si es el último chunk")


# ============================================
# WEBSOCKET SCHEMAS
# ============================================

class WSChatMessage(BaseModel):
    """Esquema de mensaje de chat por WebSocket."""
    type: str = "chat_message"
    message: str = Field(..., min_length=1, max_length=10000)
    moto_id: Optional[int] = None
    tipo_prompt: Optional[str] = "general"


class WSTypingIndicator(BaseModel):
    """Esquema para indicador de escritura."""
    type: str  # "typing_start" o "typing_stop"


class WSHistoryRequest(BaseModel):
    """Esquema para solicitar historial."""
    type: str = "get_history"
    limit: Optional[int] = Field(50, ge=1, le=200)


class WSClearHistory(BaseModel):
    """Esquema para limpiar historial."""
    type: str = "clear_history"


class WSChatResponse(BaseModel):
    """Esquema de respuesta de chat por WebSocket."""
    type: str = "chat_response"
    content: str
    role: str = "assistant"
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None
    modelo_usado: Optional[str] = None
    timestamp: str


class WSStreamChunk(BaseModel):
    """Esquema para streaming por WebSocket."""
    type: str = "stream_chunk"
    content: str
    done: bool = False


class WSError(BaseModel):
    """Esquema para errores por WebSocket."""
    type: str = "error"
    message: str
    code: Optional[str] = None


class WSHistoryResponse(BaseModel):
    """Esquema para respuesta de historial."""
    type: str = "history"
    messages: List[dict[str, Any]]
    total: int
