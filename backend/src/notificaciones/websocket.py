"""
WebSocket handler para notificaciones en tiempo real.
Push notifications a través de WebSocket.
"""
from typing import Optional, Dict, Any, List
from fastapi import WebSocket
import logging
from datetime import datetime

from src.shared.websocket import (
    BaseWebSocketHandler,
    log_websocket_event,
    WebSocketPermissionChecker,
    connection_manager,
)
from src.notificaciones.models import (
    TipoNotificacion,
    CanalNotificacion,
    EstadoNotificacion
)
from src.config.database import AsyncSessionLocal
from src.notificaciones.services import NotificacionService, PreferenciaService
from src.notificaciones.repositories import (
    NotificacionRepository,
    PreferenciaNotificacionRepository
)

logger = logging.getLogger(__name__)


class NotificacionWebSocketHandler(BaseWebSocketHandler):
    """
    Handler de WebSocket para notificaciones push en tiempo real.
    
    Características:
    - Recepción de notificaciones en tiempo real
    - Marcado de notificaciones como leídas
    - Filtrado por tipo de notificación
    - Historial de notificaciones
    - Contador de notificaciones no leídas
    
    Tipos de mensajes soportados:
    - subscribe: Suscribirse a notificaciones
    - mark_read: Marcar notificación como leída
    - mark_all_read: Marcar todas como leídas
    - get_unread_count: Obtener contador de no leídas
    - get_history: Obtener historial de notificaciones
    - filter: Configurar filtros de notificaciones
    """
    
    def __init__(self, websocket: WebSocket):
        """
        Inicializa el handler de notificaciones.
        
        Args:
            websocket: Instancia de WebSocket
        """
        super().__init__(websocket, require_auth=True)
        self.notification_filters: Dict[str, Any] = {}
        self.subscribed_types: set[TipoNotificacion] = set()
        
        # Registrar handlers
        self.register_handler("subscribe", self.handle_subscribe)
        self.register_handler("mark_read", self.handle_mark_read)
        self.register_handler("mark_all_read", self.handle_mark_all_read)
        self.register_handler("get_unread_count", self.handle_get_unread_count)
        self.register_handler("get_history", self.handle_get_history)
        self.register_handler("filter", self.handle_filter)
        self.register_handler("delete", self.handle_delete)
    
    async def on_connect(self):
        """Hook ejecutado al conectar exitosamente."""
        # Unirse a sala personal de notificaciones
        room_id = f"user_{self.user_id}_notifications"
        await connection_manager.join_room(self.user_id, room_id)
        
        logger.info(f"Usuario {self.user_id} conectado a notificaciones")
        
        # Enviar estado inicial
        async with AsyncSessionLocal() as session:
            repo = NotificacionRepository(session)
            unread_count = await repo.count_by_usuario(
                usuario_id=int(self.user_id),
                solo_no_leidas=True
            )
        
        await self.send_message({
            "type": "connection_success",
            "message": "Conectado a notificaciones",
            "unread_count": unread_count,
            "timestamp": datetime.now().isoformat()
        })
    
    @log_websocket_event("subscribe_notifications")
    async def handle_subscribe(self, data: Dict[str, Any]):
        """
        Suscribe al usuario a tipos específicos de notificaciones.
        
        Formato:
        {
            "type": "subscribe",
            "notification_types": ["ALERTA", "MANTENIMIENTO"],  // opcional, todas por defecto
            "moto_id": "uuid"  // opcional, todas las motos por defecto
        }
        """
        notification_types = data.get("notification_types", [])
        moto_id = data.get("moto_id")
        
        # Si no se especifican tipos, suscribirse a todos
        if not notification_types:
            self.subscribed_types = set(TipoNotificacion)
        else:
            # Validar y convertir tipos
            try:
                self.subscribed_types = {
                    TipoNotificacion(tipo) for tipo in notification_types
                }
            except ValueError as e:
                await self.send_error(f"Tipo de notificación inválido: {e}")
                return
        
        # Guardar filtro de moto si se especificó
        if moto_id and self.user_id:
            # Verificar propiedad de la moto
            checker = WebSocketPermissionChecker(self.user_id)
            await checker.require_moto_access(moto_id)
            self.notification_filters["moto_id"] = moto_id
        
        await self.send_message({
            "type": "subscribed",
            "notification_types": [tipo.value for tipo in self.subscribed_types],
            "filters": self.notification_filters,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(
            f"Usuario {self.user_id} suscrito a notificaciones: "
            f"{[t.value for t in self.subscribed_types]}"
        )
    
    @log_websocket_event("mark_notification_read")
    async def handle_mark_read(self, data: Dict[str, Any]):
        """
        Marca una notificación como leída.
        
        Formato:
        {
            "type": "mark_read",
            "notification_id": "uuid"
        }
        """
        notification_id = data.get("notification_id")
        
        if not notification_id:
            await self.send_error("notification_id requerido")
            return
        
        try:
            async with AsyncSessionLocal() as session:
                notificacion_repo = NotificacionRepository(session)
                preferencia_repo = PreferenciaNotificacionRepository(session)
                service = NotificacionService(notificacion_repo, preferencia_repo)
                
                # Marcar como leída
                success = await service.marcar_como_leida(
                    notificacion_id=int(notification_id)
                )
                
                if success:
                    # Obtener nuevo contador
                    unread_count = await notificacion_repo.count_by_usuario(
                        usuario_id=int(self.user_id),
                        solo_no_leidas=True
                    )
                    
                    await self.send_message({
                        "type": "marked_read",
                        "notification_id": notification_id,
                        "unread_count": unread_count,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await self.send_error("No se pudo marcar como leída")
                    
        except Exception as e:
            logger.error(f"Error marcando notificación como leída: {e}")
            await self.send_error(f"Error: {str(e)}")
    
    @log_websocket_event("mark_all_notifications_read")
    async def handle_mark_all_read(self, data: Dict[str, Any]):
        """
        Marca todas las notificaciones del usuario como leídas.
        
        Formato:
        {
            "type": "mark_all_read"
        }
        """
        try:
            async with AsyncSessionLocal() as session:
                notificacion_repo = NotificacionRepository(session)
                preferencia_repo = PreferenciaNotificacionRepository(session)
                service = NotificacionService(notificacion_repo, preferencia_repo)
                
                count = await service.marcar_todas_como_leidas(int(self.user_id))
                
                await self.send_message({
                    "type": "all_marked_read",
                    "count": count,
                    "unread_count": 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(
                    f"Usuario {self.user_id} marcó {count} notificaciones como leídas"
                )
                
        except Exception as e:
            logger.error(f"Error marcando todas como leídas: {e}")
            await self.send_error(f"Error: {str(e)}")
    
    @log_websocket_event("get_unread_count")
    async def handle_get_unread_count(self, data: Dict[str, Any]):
        """
        Obtiene el contador de notificaciones no leídas.
        
        Formato:
        {
            "type": "get_unread_count"
        }
        """
        try:
            async with AsyncSessionLocal() as session:
                repo = NotificacionRepository(session)
                unread_count = await repo.count_by_usuario(
                    usuario_id=int(self.user_id),
                    solo_no_leidas=True
                )
                
                await self.send_message({
                    "type": "unread_count",
                    "count": unread_count,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo contador: {e}")
            await self.send_error("Error obteniendo contador")
    
    @log_websocket_event("get_notification_history")
    async def handle_get_history(self, data: Dict[str, Any]):
        """
        Obtiene el historial de notificaciones.
        
        Formato:
        {
            "type": "get_history",
            "limit": 50,  // opcional
            "offset": 0,  // opcional
            "unread_only": false,  // opcional
            "notification_type": "ALERTA"  // opcional
        }
        """
        limit = int(data.get("limit", 50))
        offset = int(data.get("offset", 0))
        unread_only = bool(data.get("unread_only", False))
        notification_type = data.get("notification_type")
        
        try:
            async with AsyncSessionLocal() as session:
                repo = NotificacionRepository(session)
                
                # Obtener notificaciones usando el método correcto
                notifications = await repo.get_by_usuario(
                    usuario_id=int(self.user_id),
                    solo_no_leidas=unread_only,
                    skip=offset,
                    limit=limit
                )
                
                await self.send_message({
                    "type": "history",
                    "notifications": [
                        {
                            "id": str(notif.id),
                            "tipo": notif.tipo,
                            "titulo": notif.titulo,
                            "mensaje": notif.mensaje,
                            "leida": notif.leida,
                            "created_at": notif.created_at.isoformat(),
                            "datos_adicionales": {},
                        }
                        for notif in notifications
                    ],
                    "count": len(notifications),
                    "has_more": len(notifications) == limit,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            await self.send_error("Error obteniendo historial")
    
    @log_websocket_event("filter_notifications")
    async def handle_filter(self, data: Dict[str, Any]):
        """
        Configura filtros de notificaciones.
        
        Formato:
        {
            "type": "filter",
            "filters": {
                "moto_id": "uuid",
                "severity": "high",
                "types": ["ALERTA", "FALLA"]
            }
        }
        """
        filters = data.get("filters", {})
        
        # Validar filtro de moto si existe
        if "moto_id" in filters and self.user_id:
            checker = WebSocketPermissionChecker(self.user_id)
            await checker.require_moto_access(filters["moto_id"])
        
        self.notification_filters.update(filters)
        
        await self.send_message({
            "type": "filters_updated",
            "filters": self.notification_filters,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Filtros actualizados para usuario {self.user_id}: {filters}")
    
    @log_websocket_event("delete_notification")
    async def handle_delete(self, data: Dict[str, Any]):
        """
        Elimina una notificación.
        
        Formato:
        {
            "type": "delete",
            "notification_id": "uuid"
        }
        """
        notification_id = data.get("notification_id")
        
        if not notification_id:
            await self.send_error("notification_id requerido")
            return
        
        try:
            async with AsyncSessionLocal() as session:
                notificacion_repo = NotificacionRepository(session)
                preferencia_repo = PreferenciaNotificacionRepository(session)
                service = NotificacionService(notificacion_repo, preferencia_repo)
                
                success = await service.eliminar_notificacion(int(notification_id))
                
                if success:
                    await self.send_message({
                        "type": "deleted",
                        "notification_id": notification_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await self.send_error("No se pudo eliminar la notificación")
                    
        except Exception as e:
            logger.error(f"Error eliminando notificación: {e}")
            await self.send_error(f"Error: {str(e)}")
    
    async def send_notification(self, notification: Dict[str, Any]):
        """
        Envía una notificación push al cliente.
        
        Este método es llamado por el sistema cuando hay una nueva notificación.
        
        Args:
            notification: Diccionario con datos de la notificación
        """
        # Verificar filtros
        notification_type = notification.get("tipo")
        
        # Verificar si está suscrito a este tipo
        if self.subscribed_types and notification_type not in self.subscribed_types:
            return
        
        # Verificar filtros adicionales
        if self.notification_filters:
            # Filtro de moto
            if "moto_id" in self.notification_filters:
                if notification.get("moto_id") != self.notification_filters["moto_id"]:
                    return
            
            # Filtro de severidad
            if "severity" in self.notification_filters:
                if notification.get("severity") != self.notification_filters["severity"]:
                    return
        
        # Enviar notificación
        await self.send_message({
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.debug(
            f"Notificación enviada a usuario {self.user_id}: "
            f"{notification.get('titulo')}"
        )
    
    async def on_disconnect(self):
        """Hook ejecutado al desconectar."""
        # Salir de sala de notificaciones
        room_id = f"user_{self.user_id}_notifications"
        await connection_manager.leave_room(self.user_id, room_id)
        
        logger.info(f"Usuario {self.user_id} desconectado de notificaciones")


# ============================================
# ENDPOINT WEBSOCKET
# ============================================
async def notificacion_websocket_endpoint(websocket: WebSocket):
    """
    Endpoint de WebSocket para notificaciones.
    
    URL: /ws/notifications?token=<jwt_token>
    
    Args:
        websocket: Instancia de WebSocket
    """
    handler = NotificacionWebSocketHandler(websocket)
    await handler.handle()


# ============================================
# FUNCIONES HELPER PARA BROADCAST
# ============================================
async def send_notification_to_user(user_id: str, notification: Dict[str, Any]):
    """
    Envía una notificación push a un usuario específico.
    
    Args:
        user_id: ID del usuario
        notification: Datos de la notificación
    """
    try:
        # Enviar a través del connection manager
        message = {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
        
        await connection_manager.send_personal_message(
            message=message,
            user_id=user_id
        )
        
        logger.debug(f"Notificación enviada a usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación a usuario {user_id}: {e}")


async def broadcast_notification_to_moto_owners(
    moto_id: str,
    notification: Dict[str, Any]
):
    """
    Envía una notificación a todos los conectados a una moto.
    
    Args:
        moto_id: ID de la moto
        notification: Datos de la notificación
    """
    try:
        room_id = f"moto_{moto_id}"
        
        message = {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.now().isoformat()
        }
        
        await connection_manager.broadcast_to_room(
            message=message,
            room_id=room_id
        )
        
        logger.debug(f"Notificación broadcast a moto {moto_id}")
        
    except Exception as e:
        logger.error(f"Error en broadcast de notificación: {e}")
