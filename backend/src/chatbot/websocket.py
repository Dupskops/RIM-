"""
WebSocket handler para el chatbot.
Maneja conversaciones en tiempo real con streaming de respuestas.
"""
from typing import Optional
from fastapi import WebSocket
import logging
import json
from datetime import datetime

from src.shared.websocket import (
    BaseWebSocketHandler,
    rate_limit,
    validate_message_schema,
    log_websocket_event,
    WebSocketPermissionChecker,
)
from src.shared.constants import WSMessageType
from src.config.database import AsyncSessionLocal
from src.chatbot.services import ChatbotService
from src.chatbot.repositories import ConversacionRepository, MensajeRepository
from src.chatbot import use_cases

logger = logging.getLogger(__name__)


class ChatbotWebSocketHandler(BaseWebSocketHandler):
    """
    Handler de WebSocket para el chatbot con streaming de respuestas.
    
    Características:
    - Streaming de respuestas del LLM (Ollama)
    - Historial de conversación persistente
    - Control de acceso Freemium/Premium
    - Rate limiting por usuario
    - Typing indicators
    
    Tipos de mensajes soportados:
    - chat_message: Enviar mensaje al chatbot
    - get_history: Obtener historial de conversación
    - clear_history: Limpiar historial
    - typing_start/stop: Indicadores de escritura
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        conversation_id: Optional[str] = None
    ):
        """
        Inicializa el handler del chatbot.
        
        Args:
            websocket: Instancia de WebSocket
            conversation_id: ID de conversación existente (opcional)
        """
        super().__init__(websocket, require_auth=True)
        self.conversation_id = conversation_id
        self.access_level: Optional[str] = None  # "freemium" o "premium"
        
        # Registrar handlers de mensajes
        self.register_handler("chat_message", self.handle_chat_message)
        self.register_handler("get_history", self.handle_get_history)
        self.register_handler("clear_history", self.handle_clear_history)
        self.register_handler("typing_start", self.handle_typing_start)
        self.register_handler("typing_stop", self.handle_typing_stop)
    
    async def on_connect(self):
        """Hook ejecutado al conectar exitosamente."""
        # Verificar acceso al chatbot
        checker = WebSocketPermissionChecker(self.user_id)
        self.access_level = await checker.get_chatbot_access_level()
        
        logger.info(
            f"Usuario {self.user_id} conectado al chatbot "
            f"(nivel: {self.access_level})"
        )
        
        # Enviar mensaje de bienvenida
        await self.send_message({
            "type": "connection_success",
            "message": "Conectado al chatbot RIM",
            "access_level": self.access_level,
            "conversation_id": self.conversation_id,
            "features": {
                "streaming": True,
                "history": True,
                "advanced_analysis": self.access_level == "premium",
                "context_length": 8000 if self.access_level == "premium" else 2000,
            },
            "timestamp": datetime.now().isoformat()
        })
    
    @rate_limit(max_messages=20, window_seconds=60)  # 20 mensajes por minuto
    @validate_message_schema(["message"])
    @log_websocket_event("chat_message_received")
    async def handle_chat_message(self, data: dict):
        """
        Maneja un mensaje de chat del usuario.
        Procesa con el LLM y hace streaming de la respuesta.
        
        Formato del mensaje:
        {
            "type": "chat_message",
            "message": "¿Cuál es la presión correcta de las llantas?",
            "conversation_id": "uuid-optional",
            "context": {  // opcional
                "moto_id": "uuid",
                "current_sensors": {...}
            }
        }
        """
        message = data["message"]
        conversation_id = data.get("conversation_id", self.conversation_id)
        context = data.get("context", {})
        
        logger.info(
            f"Procesando mensaje de usuario {self.user_id}: "
            f"{message[:50]}..."
        )
        
        # Enviar indicador de "escribiendo"
        await self.send_message({
            "type": "bot_typing",
            "is_typing": True,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            async with AsyncSessionLocal() as session:
                # Inicializar repositorios y servicios
                conversacion_repo = ConversacionRepository(session)
                mensaje_repo = MensajeRepository(session)
                chatbot_service = ChatbotService(conversacion_repo, mensaje_repo)
                
                # Determinar si usar modo avanzado (Premium)
                use_advanced = (
                    self.access_level == "premium" and
                    data.get("use_advanced", False)
                )
                
                # Procesar mensaje con streaming
                response_chunks = []
                async for chunk in chatbot_service.process_message_stream(
                    usuario_id=int(self.user_id),
                    message=message,
                    conversation_id=conversation_id,
                    nivel_acceso=self.access_level or "freemium",
                    context=context
                ):
                    # Enviar chunk al cliente
                    await self.send_message({
                        "type": "chat_chunk",
                        "chunk": chunk,
                        "timestamp": datetime.now().isoformat()
                    })
                    response_chunks.append(chunk)
                
                # Respuesta completa
                full_response = "".join(response_chunks)
                
                # Enviar mensaje de finalización
                await self.send_message({
                    "type": "chat_complete",
                    "message": full_response,
                    "conversation_id": conversation_id,
                    "tokens_used": len(full_response.split()),  # Aproximado
                    "model": "premium" if use_advanced else "basic",
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(
                    f"Respuesta enviada a usuario {self.user_id} "
                    f"({len(response_chunks)} chunks)"
                )
                
        except Exception as e:
            logger.error(f"Error procesando mensaje del chatbot: {e}")
            await self.send_error(f"Error procesando tu mensaje: {str(e)}")
            
        finally:
            # Detener indicador de "escribiendo"
            await self.send_message({
                "type": "bot_typing",
                "is_typing": False,
                "timestamp": datetime.now().isoformat()
            })
    
    @log_websocket_event("get_chat_history")
    async def handle_get_history(self, data: dict):
        """
        Obtiene el historial de una conversación.
        
        Formato:
        {
            "type": "get_history",
            "conversation_id": "uuid",
            "limit": 50  // opcional
        }
        """
        conversation_id = data.get("conversation_id", self.conversation_id)
        limit = data.get("limit", 50)
        
        if not conversation_id:
            await self.send_error("conversation_id requerido")
            return
        
        try:
            async with AsyncSessionLocal() as session:
                conversacion_repo = ConversacionRepository(session)
                mensaje_repo = MensajeRepository(session)
                
                # Verificar que la conversación pertenezca al usuario
                conversacion = await conversacion_repo.get_by_conversation_id(conversation_id)
                if not conversacion or str(conversacion.usuario_id) != str(self.user_id):
                    await self.send_error("Conversación no encontrada")
                    return
                
                # Obtener mensajes
                mensajes = await mensaje_repo.get_by_conversacion(
                    conversacion.id,
                    limit=limit
                )
                
                await self.send_message({
                    "type": "history",
                    "conversation_id": conversation_id,
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.contenido,
                            "timestamp": msg.created_at.isoformat(),
                        }
                        for msg in mensajes
                    ],
                    "total": len(mensajes),
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            await self.send_error("Error obteniendo historial")
    
    @log_websocket_event("clear_chat_history")
    async def handle_clear_history(self, data: dict):
        """
        Limpia el historial de una conversación.
        
        Formato:
        {
            "type": "clear_history",
            "conversation_id": "uuid"
        }
        """
        conversation_id = data.get("conversation_id", self.conversation_id)
        
        if not conversation_id:
            await self.send_error("conversation_id requerido")
            return
        
        try:
            async with AsyncSessionLocal() as session:
                conversacion_repo = ConversacionRepository(session)
                mensaje_repo = MensajeRepository(session)
                
                # Verificar propiedad
                conversacion = await conversacion_repo.get_by_conversation_id(conversation_id)
                if not conversacion or str(conversacion.usuario_id) != str(self.user_id):
                    await self.send_error("Conversación no encontrada")
                    return
                
                # Limpiar mensajes usando el use case
                clear_use_case = use_cases.ClearHistoryUseCase(session)
                await clear_use_case.execute(
                    conversacion_id=conversacion.id,
                    usuario_id=int(self.user_id)
                )
                
                await self.send_message({
                    "type": "history_cleared",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Historial limpiado para conversación {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error limpiando historial: {e}")
            await self.send_error("Error limpiando historial")
    
    async def handle_typing_start(self, data: dict):
        """Usuario empezó a escribir (para futuros indicadores)."""
        pass  # No-op por ahora
    
    async def handle_typing_stop(self, data: dict):
        """Usuario dejó de escribir."""
        pass  # No-op por ahora
    
    async def on_disconnect(self):
        """Hook ejecutado al desconectar."""
        logger.info(
            f"Usuario {self.user_id} desconectado del chatbot "
            f"(conversación: {self.conversation_id})"
        )


# ============================================
# ENDPOINT WEBSOCKET
# ============================================
async def chatbot_websocket_endpoint(
    websocket: WebSocket,
    conversation_id: Optional[str] = None
):
    """
    Endpoint de WebSocket para el chatbot.
    
    URL: /ws/chatbot/{conversation_id}?token=<jwt_token>
    
    Args:
        websocket: Instancia de WebSocket
        conversation_id: ID de conversación (opcional)
    """
    handler = ChatbotWebSocketHandler(websocket, conversation_id)
    await handler.handle()
