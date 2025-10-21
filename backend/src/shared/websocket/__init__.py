"""
Módulo WebSocket para comunicación en tiempo real.

Proporciona:
- ConnectionManager: Gestión centralizada de conexiones WebSocket
- BaseWebSocketHandler: Clase base para handlers WebSocket personalizados
- Autenticación: Sistema de autenticación JWT para WebSocket
- Decoradores: @require_premium, @require_moto_ownership, @rate_limit, etc.
- Permisos: Verificación de permisos para recursos específicos

Ejemplo de uso básico:
    from src.shared.websocket import (
        BaseWebSocketHandler,
        connection_manager,
        require_premium
    )
    
    class ChatHandler(BaseWebSocketHandler):
        @require_premium
        async def handle_message(self, data: dict):
            message = data.get("message")
            response = await process_chat(message)
            await self.send_message({"response": response})
    
    @app.websocket("/ws/chat")
    async def chat_endpoint(websocket: WebSocket):
        handler = ChatHandler(websocket)
        await handler.handle()
"""

# Connection Manager
from .connection_manager import (
    ConnectionManager,
    connection_manager,
)

# Base Handler
from .base_handler import BaseWebSocketHandler

# Autenticación
from .auth import (
    get_token_from_websocket,
    authenticate_websocket,
    verify_websocket_permissions,
    WebSocketAuthMiddleware,
)

# Decoradores
from .decorators import (
    require_premium,
    require_moto_ownership,
    require_admin,
    log_websocket_event,
    rate_limit,
    validate_message_schema,
    auto_rejoin_room,
)

# Permisos
from .permissions import (
    check_premium_subscription,
    check_moto_ownership,
    check_admin_role,
    check_notification_permission,
    check_chatbot_access,
    check_sensor_access,
    check_maintenance_access,
    check_failure_access,
    verify_websocket_permission,
    WebSocketPermissionChecker,
)

__all__ = [
    # Connection Manager
    "ConnectionManager",
    "connection_manager",
    # Base Handler
    "BaseWebSocketHandler",
    # Autenticación
    "get_token_from_websocket",
    "authenticate_websocket",
    "verify_websocket_permissions",
    "WebSocketAuthMiddleware",
    # Decoradores
    "require_premium",
    "require_moto_ownership",
    "require_admin",
    "log_websocket_event",
    "rate_limit",
    "validate_message_schema",
    "auto_rejoin_room",
    # Permisos
    "check_premium_subscription",
    "check_moto_ownership",
    "check_admin_role",
    "check_notification_permission",
    "check_chatbot_access",
    "check_sensor_access",
    "check_maintenance_access",
    "check_failure_access",
    "verify_websocket_permission",
    "WebSocketPermissionChecker",
]
