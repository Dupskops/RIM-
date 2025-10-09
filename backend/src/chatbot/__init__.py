"""
Módulo chatbot - Asistente conversacional con IA.
"""
from src.chatbot.routes import router as chatbot_router
from src.chatbot.models import Conversacion, Mensaje
from src.chatbot.schemas import (
    # Request schemas
    ConversacionCreate,
    MensajeCreate,
    MensajeFeedback,
    ChatRequest,
    # Response schemas
    MensajeResponse,
    ConversacionResponse,
    ConversacionWithMessagesResponse,
    #ConversacionListResponse,
    ChatResponse,
    ChatStreamChunk,
    ConversacionStatsResponse,
    # Filter schemas
    ConversacionFilterParams,
    # WebSocket schemas
    WSChatMessage,
    WSTypingIndicator,
    WSHistoryRequest,
    WSClearHistory,
    WSChatResponse,
    WSStreamChunk,
    WSError,
    WSHistoryResponse,
)
from src.chatbot.events import (
    ConversacionIniciadaEvent,
    MensajeEnviadoEvent,
    RespuestaGeneradaEvent,
    FeedbackRecibidoEvent,
    ErrorChatbotEvent,
    ConversacionFinalizadaEvent,
    LimiteAlcanzadoEvent,
)
from src.chatbot.prompts.diagnostic_prompt import (
    DIAGNOSTIC_SYSTEM_PROMPT,
    build_diagnostic_prompt,
    build_quick_diagnostic_prompt,
)
from src.chatbot.prompts.maintenance_prompt import (
    MAINTENANCE_SYSTEM_PROMPT,
    build_maintenance_recommendation_prompt,
    build_maintenance_schedule_prompt,
    build_cost_optimization_prompt,
)
from src.chatbot.prompts.explanation_prompt import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt,
    build_sensor_explanation_prompt,
    build_maintenance_explanation_prompt,
)

__all__ = [
    # Router
    "chatbot_router",
    # Models
    "Conversacion",
    "Mensaje",
    # Request Schemas
    "ConversacionCreate",
    "MensajeCreate",
    "MensajeFeedback",
    "ChatRequest",
    # Response Schemas
    "MensajeResponse",
    "ConversacionResponse",
    "ConversacionWithMessagesResponse",
    "ChatResponse",
    "ChatStreamChunk",
    "ConversacionStatsResponse",
    # Filter Schemas
    "ConversacionFilterParams",
    # WebSocket Schemas
    "WSChatMessage",
    "WSTypingIndicator",
    "WSHistoryRequest",
    "WSClearHistory",
    "WSChatResponse",
    "WSStreamChunk",
    "WSError",
    "WSHistoryResponse",
    # Events
    "ConversacionIniciadaEvent",
    "MensajeEnviadoEvent",
    "RespuestaGeneradaEvent",
    "FeedbackRecibidoEvent",
    "ErrorChatbotEvent",
    "ConversacionFinalizadaEvent",
    "LimiteAlcanzadoEvent",
    # Prompt Functions
    "DIAGNOSTIC_SYSTEM_PROMPT",
    "build_diagnostic_prompt",
    "build_quick_diagnostic_prompt",
    "MAINTENANCE_SYSTEM_PROMPT",
    "build_maintenance_recommendation_prompt",
    "build_maintenance_schedule_prompt",
    "build_cost_optimization_prompt",
    "EXPLANATION_SYSTEM_PROMPT",
    "build_explanation_prompt",
    "build_sensor_explanation_prompt",
    "build_maintenance_explanation_prompt",
]
