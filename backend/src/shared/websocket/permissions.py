"""
Sistema de permisos para WebSocket.
Funciones para verificar permisos específicos en operaciones WebSocket.
"""
from typing import Optional
import logging

from ..exceptions import ForbiddenException, UnauthorizedException
from ..constants import TipoSuscripcion

logger = logging.getLogger(__name__)


async def check_premium_subscription(user_id: str) -> bool:
    """
    Verifica si el usuario tiene suscripción Premium activa.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        True si tiene Premium activo, False en caso contrario
    """
    from src.suscripciones.repositories import SuscripcionRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        repo = SuscripcionRepository(session)
        suscripcion = await repo.get_by_user_id(user_id)
        
        if not suscripcion:
            return False
        
        return (
            suscripcion.tipo == TipoSuscripcion.PREMIUM and
            suscripcion.activa
        )


async def check_moto_ownership(user_id: str, moto_id: str) -> bool:
    """
    Verifica si el usuario es dueño de la moto especificada.
    
    Args:
        user_id: ID del usuario
        moto_id: ID de la moto
        
    Returns:
        True si es dueño, False en caso contrario
    """
    from src.motos.repositories import MotoRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        repo = MotoRepository(session)
        moto = await repo.get_by_id(moto_id)
        
        if not moto:
            return False
        
        return str(moto.usuario_id) == str(user_id)


async def check_admin_role(user_id: str) -> bool:
    """
    Verifica si el usuario tiene rol de administrador.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        True si es admin, False en caso contrario
    """
    from src.usuarios.repositories import UsuarioRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        repo = UsuarioRepository(session)
        usuario = await repo.get_by_id(user_id)
        
        if not usuario:
            return False
        
        return usuario.rol == "admin"


async def check_notification_permission(user_id: str, notification_id: str) -> bool:
    """
    Verifica si el usuario puede acceder a una notificación específica.
    
    Args:
        user_id: ID del usuario
        notification_id: ID de la notificación
        
    Returns:
        True si tiene permiso, False en caso contrario
    """
    from src.notificaciones.repositories import NotificacionRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        repo = NotificacionRepository(session)
        notificacion = await repo.get_by_id(notification_id)
        
        if not notificacion:
            return False
        
        return str(notificacion.usuario_id) == str(user_id)


async def check_chatbot_access(user_id: str) -> tuple[bool, Optional[str]]:
    """
    Verifica si el usuario puede acceder al chatbot.
    Retorna también el nivel de acceso (freemium/premium).
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Tupla (puede_acceder, nivel_acceso)
        nivel_acceso puede ser: "freemium", "premium", None
    """
    from src.suscripciones.repositories import SuscripcionRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        repo = SuscripcionRepository(session)
        suscripcion = await repo.get_by_user_id(user_id)
        
        if not suscripcion or not suscripcion.activa:
            return False, None
        
        nivel = (
            "premium" if suscripcion.tipo == TipoSuscripcion.PREMIUM
            else "freemium"
        )
        
        return True, nivel


async def check_sensor_access(user_id: str, sensor_id: str) -> bool:
    """
    Verifica si el usuario puede acceder a los datos de un sensor.
    El usuario debe ser dueño de la moto asociada al sensor.
    
    Args:
        user_id: ID del usuario
        sensor_id: ID del sensor
        
    Returns:
        True si tiene permiso, False en caso contrario
    """
    from src.sensores.repositories import SensorRepository
    from src.motos.repositories import MotoRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        sensor_repo = SensorRepository(session)
        sensor = await sensor_repo.get_by_id(sensor_id)
        
        if not sensor:
            return False
        
        moto_repo = MotoRepository(session)
        moto = await moto_repo.get_by_id(sensor.moto_id)
        
        if not moto:
            return False
        
        return str(moto.usuario_id) == str(user_id)


async def check_maintenance_access(user_id: str, mantenimiento_id: str) -> bool:
    """
    Verifica si el usuario puede acceder a un registro de mantenimiento.
    El usuario debe ser dueño de la moto asociada.
    
    Args:
        user_id: ID del usuario
        mantenimiento_id: ID del mantenimiento
        
    Returns:
        True si tiene permiso, False en caso contrario
    """
    from src.mantenimiento.repositories import MantenimientoRepository
    from src.motos.repositories import MotoRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        mant_repo = MantenimientoRepository(session)
        mantenimiento = await mant_repo.get_by_id(mantenimiento_id)
        
        if not mantenimiento:
            return False
        
        moto_repo = MotoRepository(session)
        moto = await moto_repo.get_by_id(mantenimiento.moto_id)
        
        if not moto:
            return False
        
        return str(moto.usuario_id) == str(user_id)


async def check_failure_access(user_id: str, falla_id: str) -> bool:
    """
    Verifica si el usuario puede acceder a un registro de falla.
    El usuario debe ser dueño de la moto asociada.
    
    Args:
        user_id: ID del usuario
        falla_id: ID de la falla
        
    Returns:
        True si tiene permiso, False en caso contrario
    """
    from src.fallas.repositories import FallaRepository
    from src.motos.repositories import MotoRepository
    from src.config.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        falla_repo = FallaRepository(session)
        falla = await falla_repo.get_by_id(falla_id)
        
        if not falla:
            return False
        
        moto_repo = MotoRepository(session)
        moto = await moto_repo.get_by_id(falla.moto_id)
        
        if not moto:
            return False
        
        return str(moto.usuario_id) == str(user_id)


async def verify_websocket_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    raise_exception: bool = True
) -> bool:
    """
    Función genérica para verificar permisos en WebSocket.
    
    Args:
        user_id: ID del usuario
        resource_type: Tipo de recurso ("moto", "sensor", "notification", etc.)
        resource_id: ID del recurso
        raise_exception: Si True, lanza excepción en caso de falta de permisos
        
    Returns:
        True si tiene permiso
        
    Raises:
        ForbiddenException: Si no tiene permiso y raise_exception=True
    """
    permission_map = {
        "moto": check_moto_ownership,
        "sensor": check_sensor_access,
        "notification": check_notification_permission,
        "maintenance": check_maintenance_access,
        "failure": check_failure_access,
    }
    
    check_func = permission_map.get(resource_type)
    
    if not check_func:
        logger.warning(f"Tipo de recurso desconocido: {resource_type}")
        if raise_exception:
            raise ValueError(f"Tipo de recurso desconocido: {resource_type}")
        return False
    
    has_permission = await check_func(user_id, resource_id)
    
    if not has_permission and raise_exception:
        raise ForbiddenException(
            f"No tienes permiso para acceder a este recurso ({resource_type})"
        )
    
    return has_permission


class WebSocketPermissionChecker:
    """
    Clase helper para verificar permisos en handlers de WebSocket.
    
    Uso:
        checker = WebSocketPermissionChecker(user_id)
        await checker.require_moto_access(moto_id)
        await checker.require_premium()
    """
    
    def __init__(self, user_id: str):
        """
        Inicializa el checker con un usuario.
        
        Args:
            user_id: ID del usuario
        """
        self.user_id = user_id
    
    async def require_premium(self):
        """
        Verifica suscripción Premium, lanza excepción si no la tiene.
        
        Raises:
            ForbiddenException: Si no tiene Premium activo
        """
        has_premium = await check_premium_subscription(self.user_id)
        if not has_premium:
            raise ForbiddenException(
                "Esta funcionalidad requiere suscripción Premium"
            )
    
    async def require_moto_access(self, moto_id: str):
        """
        Verifica acceso a moto, lanza excepción si no es dueño.
        
        Args:
            moto_id: ID de la moto
            
        Raises:
            ForbiddenException: Si no es dueño
        """
        has_access = await check_moto_ownership(self.user_id, moto_id)
        if not has_access:
            raise ForbiddenException(
                "No tienes permiso para acceder a esta moto"
            )
    
    async def require_admin(self):
        """
        Verifica rol admin, lanza excepción si no es admin.
        
        Raises:
            ForbiddenException: Si no es administrador
        """
        is_admin = await check_admin_role(self.user_id)
        if not is_admin:
            raise ForbiddenException(
                "Se requieren permisos de administrador"
            )
    
    async def require_sensor_access(self, sensor_id: str):
        """
        Verifica acceso a sensor, lanza excepción si no tiene permiso.
        
        Args:
            sensor_id: ID del sensor
            
        Raises:
            ForbiddenException: Si no tiene permiso
        """
        has_access = await check_sensor_access(self.user_id, sensor_id)
        if not has_access:
            raise ForbiddenException(
                "No tienes permiso para acceder a este sensor"
            )
    
    async def get_chatbot_access_level(self) -> str:
        """
        Obtiene el nivel de acceso al chatbot.
        
        Returns:
            "freemium", "premium" o lanza excepción si no tiene acceso
            
        Raises:
            ForbiddenException: Si no tiene acceso al chatbot
        """
        can_access, level = await check_chatbot_access(self.user_id)
        if not can_access:
            raise ForbiddenException(
                "No tienes una suscripción activa para usar el chatbot"
            )
        return level
