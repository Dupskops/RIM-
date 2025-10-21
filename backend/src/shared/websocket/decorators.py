"""
Decoradores para WebSocket.
Decoradores para controlar acceso, validación y logging en handlers WebSocket.
"""
from typing import Callable, Optional
from functools import wraps
import logging
from datetime import datetime

from ..exceptions import (
    UnauthorizedException,
    ForbiddenException,
    PremiumFeatureException
)
from ..constants import TipoSuscripcion

logger = logging.getLogger(__name__)


def require_premium(func: Callable):
    """
    Decorador que requiere suscripción Premium para usar la feature.
    
    Uso en handlers de WebSocket:
        class ChatHandler(BaseWebSocketHandler):
            @require_premium
            async def handle_advanced_analysis(self, data: dict):
                # Solo usuarios Premium pueden ejecutar esto
                ...
    
    Verifica que self.user_id tenga suscripción Premium activa.
    Lanza PremiumFeatureException si no cumple.
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Lazy import para evitar circular dependency
        from src.suscripciones.repositories import SuscripcionRepository
        from src.config.database import AsyncSessionLocal
        
        if not hasattr(self, 'user_id') or not self.user_id:
            raise UnauthorizedException("Usuario no autenticado")
        
        # Verificar suscripción
        async with AsyncSessionLocal() as session:
            repo = SuscripcionRepository(session)
            suscripcion = await repo.get_by_user_id(self.user_id)
            
            if not suscripcion or suscripcion.tipo != TipoSuscripcion.PREMIUM:
                await self.send_error(
                    "Esta funcionalidad requiere suscripción Premium"
                )
                raise PremiumFeatureException(
                    "Se requiere suscripción Premium para esta feature"
                )
            
            if not suscripcion.activa:
                await self.send_error("Tu suscripción Premium ha expirado")
                raise PremiumFeatureException("Suscripción Premium expirada")
        
        return await func(self, *args, **kwargs)
    
    return wrapper


def require_moto_ownership(moto_id_param: str = "moto_id"):
    """
    Decorador que verifica que el usuario sea dueño de la moto.
    
    Args:
        moto_id_param: Nombre del parámetro que contiene el ID de moto
        
    Uso:
        @require_moto_ownership("moto_id")
        async def handle_sensor_data(self, data: dict):
            moto_id = data["moto_id"]
            # Solo el dueño puede ver sensores de su moto
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, data: dict, *args, **kwargs):
            # Lazy import para evitar circular dependency
            from src.motos.repositories import MotoRepository
            from src.config.database import AsyncSessionLocal
            
            if not hasattr(self, 'user_id') or not self.user_id:
                raise UnauthorizedException("Usuario no autenticado")
            
            # Obtener moto_id del mensaje
            moto_id = data.get(moto_id_param)
            if not moto_id:
                await self.send_error(f"Falta parámetro: {moto_id_param}")
                raise ValueError(f"Parámetro {moto_id_param} requerido")
            
            # Verificar propiedad
            async with AsyncSessionLocal() as session:
                repo = MotoRepository(session)
                moto = await repo.get_by_id(moto_id)
                
                if not moto:
                    await self.send_error("Moto no encontrada")
                    raise ValueError("Moto no existe")
                
                if str(moto.usuario_id) != str(self.user_id):
                    await self.send_error(
                        "No tienes permiso para acceder a esta moto"
                    )
                    raise ForbiddenException(
                        "Usuario no es dueño de la moto"
                    )
            
            return await func(self, data, *args, **kwargs)
        
        return wrapper
    return decorator


def require_admin(func: Callable):
    """
    Decorador que requiere rol de administrador.
    
    Uso:
        @require_admin
        async def handle_admin_command(self, data: dict):
            # Solo admins pueden ejecutar esto
            ...
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Lazy import para evitar circular dependency
        from src.usuarios.repositories import UsuarioRepository
        from src.config.database import AsyncSessionLocal
        
        if not hasattr(self, 'user_id') or not self.user_id:
            raise UnauthorizedException("Usuario no autenticado")
        
        # Verificar rol admin
        async with AsyncSessionLocal() as session:
            repo = UsuarioRepository(session)
            usuario = await repo.get_by_id(self.user_id)
            
            if not usuario or usuario.rol != "admin":
                await self.send_error(
                    "Se requieren permisos de administrador"
                )
                raise ForbiddenException("Usuario no es administrador")
        
        return await func(self, *args, **kwargs)
    
    return wrapper


def log_websocket_event(event_name: Optional[str] = None):
    """
    Decorador para logging automático de eventos WebSocket.
    
    Args:
        event_name: Nombre del evento (opcional, usa nombre de función si no se especifica)
        
    Uso:
        @log_websocket_event("chat_message_sent")
        async def handle_message(self, data: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            name = event_name or func.__name__
            user = getattr(self, 'user_id', 'unknown')
            
            logger.info(
                f"[WS Event] {name} | User: {user} | "
                f"Time: {datetime.now().isoformat()}"
            )
            
            try:
                result = await func(self, *args, **kwargs)
                logger.debug(f"[WS Event] {name} completado exitosamente")
                return result
            except Exception as e:
                logger.error(f"[WS Event] {name} falló: {e}")
                raise
        
        return wrapper
    return decorator


def rate_limit(max_messages: int, window_seconds: int):
    """
    Decorador para limitar tasa de mensajes (rate limiting).
    
    Args:
        max_messages: Número máximo de mensajes permitidos
        window_seconds: Ventana de tiempo en segundos
        
    Uso:
        @rate_limit(max_messages=10, window_seconds=60)
        async def handle_message(self, data: dict):
            # Máximo 10 mensajes por minuto
            ...
    
    Nota: Usa un diccionario en memoria. Para producción considerar Redis.
    """
    # Almacenamiento en memoria: {user_id: [timestamps]}
    _message_counts = {}
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'user_id') or not self.user_id:
                return await func(self, *args, **kwargs)
            
            user_id = self.user_id
            now = datetime.now().timestamp()
            
            # Inicializar si no existe
            if user_id not in _message_counts:
                _message_counts[user_id] = []
            
            # Limpiar timestamps antiguos
            cutoff = now - window_seconds
            _message_counts[user_id] = [
                ts for ts in _message_counts[user_id]
                if ts > cutoff
            ]
            
            # Verificar límite
            if len(_message_counts[user_id]) >= max_messages:
                await self.send_error(
                    f"Límite de mensajes excedido. "
                    f"Máximo {max_messages} mensajes cada {window_seconds} segundos."
                )
                logger.warning(
                    f"Rate limit excedido para usuario {user_id}: "
                    f"{len(_message_counts[user_id])} mensajes"
                )
                return
            
            # Agregar timestamp actual
            _message_counts[user_id].append(now)
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def validate_message_schema(required_fields: list):
    """
    Decorador para validar esquema de mensaje.
    
    Args:
        required_fields: Lista de campos requeridos en el mensaje
        
    Uso:
        @validate_message_schema(["message", "conversation_id"])
        async def handle_chat(self, data: dict):
            # Garantizado que data tiene "message" y "conversation_id"
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, data: dict, *args, **kwargs):
            # Verificar campos requeridos
            missing = [field for field in required_fields if field not in data]
            
            if missing:
                await self.send_error(
                    f"Campos requeridos faltantes: {', '.join(missing)}"
                )
                raise ValueError(f"Campos faltantes: {missing}")
            
            return await func(self, data, *args, **kwargs)
        
        return wrapper
    return decorator


def auto_rejoin_room(func: Callable):
    """
    Decorador que automáticamente reintenta unirse a una sala si falla.
    
    Uso:
        @auto_rejoin_room
        async def handle_room_message(self, data: dict):
            # Si hay error de sala, reintenta unirse automáticamente
            ...
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        from .connection_manager import connection_manager
        
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            # Si el error es de sala y tenemos room_id, reintentar
            if "room" in str(e).lower() and hasattr(self, 'room_id'):
                logger.info(
                    f"Reintentando unirse a sala {self.room_id} "
                    f"para usuario {self.user_id}"
                )
                await connection_manager.join_room(self.user_id, self.room_id)
                return await func(self, *args, **kwargs)
            else:
                raise
    
    return wrapper