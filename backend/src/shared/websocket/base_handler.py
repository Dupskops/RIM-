"""
Handler base para WebSocket.
Proporciona estructura común para handlers de WebSocket.
"""
from typing import Optional, Callable, Dict, Any
from fastapi import WebSocket
import json
import logging
from datetime import datetime

from .connection_manager import connection_manager
from .auth import authenticate_websocket
from ..constants import WSMessageType

logger = logging.getLogger(__name__)


class BaseWebSocketHandler:
    """
    Clase base para manejar conexiones WebSocket.
    
    Proporciona:
    - Autenticación automática
    - Manejo de mensajes estructurado
    - Heartbeat/ping-pong
    - Manejo de errores
    - Desconexión limpia
    
    Ejemplo de uso:
        class ChatHandler(BaseWebSocketHandler):
            async def handle_message(self, data: dict):
                message = data.get("message")
                # Procesar mensaje...
                await self.send_message({
                    "type": "chat_response",
                    "response": "Respuesta del chatbot"
                })
        
        @app.websocket("/ws/chat")
        async def chat_endpoint(websocket: WebSocket):
            handler = ChatHandler(websocket)
            await handler.handle()
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        require_auth: bool = True,
        room_id: Optional[str] = None
    ):
        """
        Inicializa el handler.
        
        Args:
            websocket: Instancia de WebSocket
            require_auth: Si requiere autenticación (default: True)
            room_id: ID de sala para unirse automáticamente (opcional)
        """
        self.websocket = websocket
        self.require_auth = require_auth
        self.room_id = room_id
        self.user_id: Optional[str] = None
        self.is_connected = False
        self.message_handlers: Dict[str, Callable] = {}
    
    async def handle(self):
        """
        Maneja el ciclo de vida completo de la conexión WebSocket.
        Este es el método principal a llamar.
        """
        try:
            # 1. Autenticación
            if self.require_auth:
                self.user_id = await authenticate_websocket(self.websocket)
                if not self.user_id:
                    return  # Autenticación falló, conexión cerrada
            else:
                # Sin autenticación, aceptar conexión directamente
                await self.websocket.accept()
                self.user_id = "anonymous"
            
            # 2. Conectar al connection manager
            await connection_manager.connect(
                self.websocket,
                self.user_id,
                metadata={"handler": self.__class__.__name__}
            )
            self.is_connected = True
            
            # 3. Unirse a sala si se especificó
            if self.room_id:
                await connection_manager.join_room(self.user_id, self.room_id)
            
            # 4. Hook de conexión exitosa
            await self.on_connect()
            
            # 5. Loop de recepción de mensajes
            await self.message_loop()
            
        except Exception as e:
            logger.error(f"Error en WebSocket handler: {e}", exc_info=True)
            await self.on_error(e)
        finally:
            # 6. Limpieza al desconectar
            await self.cleanup()
    
    async def message_loop(self):
        """Loop principal para recibir y procesar mensajes."""
        while self.is_connected:
            try:
                # Recibir mensaje
                raw_data = await self.websocket.receive_text()
                
                # Parsear JSON
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    await self.send_error("Invalid JSON format")
                    continue
                
                # Obtener tipo de mensaje
                message_type = data.get("type")
                
                # Manejar ping/pong
                if message_type == WSMessageType.PING:
                    await self.send_message({
                        "type": WSMessageType.PONG,
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # Llamar a handler específico
                if message_type and message_type in self.message_handlers:
                    await self.message_handlers[message_type](data)
                else:
                    # Llamar a handler genérico
                    await self.handle_message(data)
                
            except Exception as e:
                if "WebSocket" in str(e):
                    # Cliente desconectado
                    logger.info(f"Cliente {self.user_id} desconectado")
                    break
                else:
                    logger.error(f"Error procesando mensaje: {e}")
                    await self.send_error(f"Error: {str(e)}")
    
    async def handle_message(self, data: dict):
        """
        Handler genérico de mensajes.
        Sobreescribir en clases hijas para procesar mensajes.
        
        Args:
            data: Diccionario con el mensaje recibido
        """
        logger.warning(
            f"Mensaje no manejado: {data.get('type', 'unknown')} "
            f"de usuario {self.user_id}"
        )
    
    async def send_message(self, data: dict):
        """
        Envía un mensaje al cliente.
        
        Args:
            data: Diccionario con el mensaje a enviar
        """
        try:
            message = json.dumps(data)
            await self.websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
    
    async def send_error(self, error_message: str):
        """
        Envía un mensaje de error al cliente.
        
        Args:
            error_message: Mensaje de error
        """
        await self.send_message({
            "type": WSMessageType.ERROR,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        Registra un handler para un tipo de mensaje específico.
        
        Args:
            message_type: Tipo de mensaje a manejar
            handler: Función async para manejar el mensaje
            
        Ejemplo:
            handler.register_handler("chat_message", self.handle_chat)
        """
        self.message_handlers[message_type] = handler
    
    async def on_connect(self):
        """
        Hook llamado cuando la conexión es exitosa.
        Sobreescribir en clases hijas para lógica personalizada.
        """
        logger.info(f"Cliente {self.user_id} conectado")
    
    async def on_disconnect(self):
        """
        Hook llamado cuando el cliente se desconecta.
        Sobreescribir en clases hijas para lógica personalizada.
        """
        logger.info(f"Cliente {self.user_id} desconectado")
    
    async def on_error(self, error: Exception):
        """
        Hook llamado cuando ocurre un error.
        Sobreescribir en clases hijas para lógica personalizada.
        
        Args:
            error: Excepción que ocurrió
        """
        logger.error(f"Error para usuario {self.user_id}: {error}")
    
    async def cleanup(self):
        """Limpieza al desconectar."""
        if self.is_connected:
            # Salir de sala si estaba en una
            if self.room_id and self.user_id:
                await connection_manager.leave_room(self.user_id, self.room_id)
            
            # Desconectar del connection manager
            await connection_manager.disconnect(self.websocket)
            
            # Hook de desconexión
            await self.on_disconnect()
            
            self.is_connected = False
