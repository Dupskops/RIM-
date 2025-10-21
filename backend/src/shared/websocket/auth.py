"""
Autenticación para WebSocket.
Maneja validación de tokens JWT en conexiones WebSocket.
"""
from typing import Optional
from fastapi import WebSocket, status
from jose import jwt, JWTError
import logging

from ...config.settings import settings
from ..exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


async def get_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Extrae el token JWT de los query params o headers del WebSocket.
    
    Args:
        websocket: Instancia de WebSocket
        
    Returns:
        Token JWT o None
        
    Uso en endpoint:
        @app.websocket("/ws/chat")
        async def websocket_endpoint(websocket: WebSocket):
            token = await get_token_from_websocket(websocket)
            ...
    
    Conexión desde cliente:
        # Opción 1: Query param
        ws = new WebSocket("ws://localhost:8000/ws/chat?token=<jwt_token>")
        
        # Opción 2: Subprotocol (headers)
        ws = new WebSocket("ws://localhost:8000/ws/chat", ["Bearer", "<jwt_token>"])
    """
    # Intentar obtener desde query params
    token = websocket.query_params.get("token")
    if token:
        return token
    
    # Intentar obtener desde headers (Sec-WebSocket-Protocol)
    headers = dict(websocket.headers)
    auth_header = headers.get("authorization") or headers.get("sec-websocket-protocol")
    
    if auth_header:
        # Formato: "Bearer <token>" o "Bearer,<token>"
        parts = auth_header.replace(",", " ").split()
        if len(parts) >= 2 and parts[0].lower() == "bearer":
            return parts[1]
    
    return None


async def decode_websocket_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT para WebSocket.
    
    Args:
        token: Token JWT
        
    Returns:
        Payload del token
        
    Raises:
        UnauthorizedException: Si el token es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise UnauthorizedException(f"Token inválido: {str(e)}")


async def authenticate_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Autentica una conexión WebSocket y retorna el user_id.
    
    Args:
        websocket: Instancia de WebSocket
        
    Returns:
        user_id si la autenticación es exitosa, None si no
        
    Raises:
        WebSocketDisconnect: Si el token es inválido (cierra la conexión)
        
    Uso:
        @app.websocket("/ws/protected")
        async def protected_websocket(websocket: WebSocket):
            user_id = await authenticate_websocket(websocket)
            if not user_id:
                return  # Conexión ya cerrada
            
            # Usuario autenticado, continuar...
            await connection_manager.connect(websocket, user_id)
    """
    try:
        # Obtener token
        token = await get_token_from_websocket(websocket)
        
        if not token:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Token de autenticación requerido"
            )
            return None
        
        # Validar token
        payload = await decode_websocket_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Token inválido: falta user_id"
            )
            return None
        
        logger.info(f"WebSocket autenticado para usuario {user_id}")
        return user_id
        
    except UnauthorizedException as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e.detail)
        )
        return None
    except Exception as e:
        logger.error(f"Error autenticando WebSocket: {e}")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Error de autenticación"
        )
        return None


async def verify_websocket_permissions(
    user_id: str,
    required_feature: Optional[str] = None
) -> bool:
    """
    Verifica si un usuario tiene permisos para usar una feature de WebSocket.
    
    Args:
        user_id: ID del usuario
        required_feature: Feature requerida (ej: "chatbot_avanzado")
        
    Returns:
        True si tiene permisos, False si no
        
    Uso:
        @app.websocket("/ws/chatbot")
        async def chatbot_websocket(websocket: WebSocket):
            user_id = await authenticate_websocket(websocket)
            if not user_id:
                return
            
            # Verificar si tiene acceso al chatbot avanzado (Premium)
            has_access = await verify_websocket_permissions(
                user_id,
                required_feature="chatbot_avanzado"
            )
            
            if not has_access:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Se requiere plan Premium"
                )
                return
    """
    if not required_feature:
        return True  # Sin restricción
    
    # TODO: Implementar verificación real contra suscripciones
    # Por ahora, retornar True (permitir todo)
    # Cuando se implemente suscripciones:
    # from ...suscripciones.services import check_user_has_feature
    # return await check_user_has_feature(user_id, required_feature)
    
    logger.warning(
        f"Verificación de permisos WS no implementada aún. "
        f"Usuario {user_id}, feature {required_feature}"
    )
    return True


class WebSocketAuthMiddleware:
    """
    Middleware para autenticación automática en WebSocket.
    
    Uso:
        @app.websocket("/ws/data")
        async def data_websocket(websocket: WebSocket):
            async with WebSocketAuthMiddleware(websocket) as user_id:
                if not user_id:
                    return  # Autenticación falló
                
                # Usuario autenticado
                await connection_manager.connect(websocket, user_id)
                # ... resto del handler
    """
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.user_id: Optional[str] = None
    
    async def __aenter__(self):
        """Autentica al conectar."""
        self.user_id = await authenticate_websocket(self.websocket)
        return self.user_id
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Limpieza al desconectar."""
        if exc_type:
            logger.error(
                f"Error en WebSocket para usuario {self.user_id}: "
                f"{exc_type.__name__}: {exc_val}"
            )
        return False  # No suprimir excepciones
