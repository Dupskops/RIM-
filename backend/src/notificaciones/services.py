"""
Servicios para el módulo de notificaciones.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from src.notificaciones.models import (
    Notificacion,
    PreferenciaNotificacion,
    CanalNotificacion,
    TipoNotificacion,
    EstadoNotificacion
)
from src.notificaciones.repositories import (
    NotificacionRepository,
    PreferenciaNotificacionRepository
)
from src.notificaciones.validators import (
    puede_enviar_notificacion,
    validate_notificacion_data,
    validate_referencia
)

logger = logging.getLogger(__name__)


class NotificacionService:
    """Servicio para gestionar notificaciones."""

    def __init__(
        self,
        notificacion_repo: NotificacionRepository,
        preferencia_repo: PreferenciaNotificacionRepository
    ):
        self.notificacion_repo = notificacion_repo
        self.preferencia_repo = preferencia_repo

    async def crear_notificacion(
        self,
        usuario_id: int,
        titulo: str,
        mensaje: Optional[str],
        tipo: TipoNotificacion,
        canal: CanalNotificacion,
        datos_adicionales: Optional[Dict[str, Any]] = None,
        accion_url: Optional[str] = None,
        accion_tipo: Optional[str] = None,
        referencia_tipo: Optional[str] = None,
        referencia_id: Optional[int] = None,
        expira_en: Optional[datetime] = None
    ) -> Notificacion:
        """Crea una nueva notificación."""
        # Validar datos
        validate_notificacion_data(titulo, mensaje, accion_url)
        validate_referencia(referencia_tipo, referencia_id)
        
        # Crear notificación
        notificacion = Notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            canal=canal,
            datos_adicionales=datos_adicionales or {},
            accion_url=accion_url,
            accion_tipo=accion_tipo,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            expira_en=expira_en
        )
        
        return await self.notificacion_repo.create(notificacion)

    async def crear_notificaciones_masivas(
        self,
        usuarios_ids: List[int],
        titulo: str,
        mensaje: Optional[str],
        tipo: TipoNotificacion,
        canal: CanalNotificacion,
        datos_adicionales: Optional[Dict[str, Any]] = None,
        accion_url: Optional[str] = None,
        accion_tipo: Optional[str] = None,
        expira_en: Optional[datetime] = None
    ) -> List[Notificacion]:
        """Crea notificaciones para múltiples usuarios."""
        # Validar datos
        validate_notificacion_data(titulo, mensaje, accion_url)
        
        # Crear notificaciones
        notificaciones = []
        for usuario_id in usuarios_ids:
            notif = Notificacion(
                usuario_id=usuario_id,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                canal=canal,
                datos_adicionales=datos_adicionales or {},
                accion_url=accion_url,
                accion_tipo=accion_tipo,
                expira_en=expira_en
            )
            notificaciones.append(notif)
        
        return await self.notificacion_repo.create_many(notificaciones)

    async def enviar_notificacion(self, notificacion_id: int) -> bool:
        """Envía una notificación."""
        notificacion = await self.notificacion_repo.get_by_id(notificacion_id)
        if not notificacion:
            logger.error(f"Notificación {notificacion_id} no encontrada")
            return False
        
        # Verificar si no está expirada
        if notificacion.esta_expirada:
            logger.warning(f"Notificación {notificacion_id} expirada")
            notificacion.estado = EstadoNotificacion.FALLIDA
            await self.notificacion_repo.update(notificacion)
            return False
        
        # Obtener preferencias del usuario
        preferencia = await self.preferencia_repo.get_or_create(notificacion.usuario_id)
        
        # Verificar si se puede enviar
        puede_enviar, razon = puede_enviar_notificacion(
            preferencia,
            notificacion.canal,
            notificacion.tipo
        )
        
        if not puede_enviar:
            logger.info(
                f"No se puede enviar notificación {notificacion_id}: {razon}"
            )
            return False
        
        # Enviar según canal
        try:
            if notificacion.canal == CanalNotificacion.IN_APP:
                # Las notificaciones in-app se consideran enviadas al crearse
                exito = True
            elif notificacion.canal == CanalNotificacion.EMAIL:
                exito = await self._enviar_email(notificacion)
            elif notificacion.canal == CanalNotificacion.PUSH:
                exito = await self._enviar_push(notificacion)
            elif notificacion.canal == CanalNotificacion.SMS:
                exito = await self._enviar_sms(notificacion)
            else:
                exito = False
            
            if exito:
                notificacion.marcar_como_enviada()
            else:
                notificacion.marcar_como_fallida("Error al enviar")
            
            await self.notificacion_repo.update(notificacion)
            return exito
            
        except Exception as e:
            logger.error(f"Error enviando notificación {notificacion_id}: {e}")
            notificacion.marcar_como_fallida(str(e))
            await self.notificacion_repo.update(notificacion)
            return False

    async def reintentar_fallidas(self, limite: int = 50) -> int:
        """Reintenta enviar notificaciones fallidas."""
        notificaciones = await self.notificacion_repo.get_fallidas_reintentables(
            limit=limite
        )
        
        exitosas = 0
        for notificacion in notificaciones:
            if await self.enviar_notificacion(notificacion.id):
                exitosas += 1
        
        return exitosas

    async def procesar_pendientes(self, limite: int = 100) -> int:
        """Procesa notificaciones pendientes de envío."""
        notificaciones = await self.notificacion_repo.get_pendientes_envio(
            limit=limite
        )
        
        exitosas = 0
        for notificacion in notificaciones:
            if await self.enviar_notificacion(notificacion.id):
                exitosas += 1
        
        return exitosas

    async def marcar_como_leida(self, notificacion_id: int) -> bool:
        """Marca una notificación como leída."""
        return await self.notificacion_repo.marcar_como_leida(notificacion_id)

    async def marcar_varias_como_leidas(self, notificacion_ids: List[int]) -> int:
        """Marca varias notificaciones como leídas."""
        return await self.notificacion_repo.marcar_varias_como_leidas(notificacion_ids)

    async def marcar_todas_como_leidas(self, usuario_id: int) -> int:
        """Marca todas las notificaciones de un usuario como leídas."""
        return await self.notificacion_repo.marcar_todas_como_leidas(usuario_id)

    async def obtener_notificaciones(
        self,
        usuario_id: int,
        solo_no_leidas: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Notificacion], int]:
        """Obtiene notificaciones de un usuario con paginación."""
        notificaciones = await self.notificacion_repo.get_by_usuario(
            usuario_id=usuario_id,
            solo_no_leidas=solo_no_leidas,
            skip=skip,
            limit=limit
        )
        
        total = await self.notificacion_repo.count_by_usuario(
            usuario_id=usuario_id,
            solo_no_leidas=solo_no_leidas
        )
        
        return notificaciones, total

    async def obtener_estadisticas(self, usuario_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de notificaciones de un usuario."""
        return await self.notificacion_repo.get_stats(usuario_id)

    async def eliminar_notificacion(self, notificacion_id: int) -> bool:
        """Elimina una notificación."""
        return await self.notificacion_repo.delete(notificacion_id)

    async def limpiar_antiguas(self, dias: int = 30) -> int:
        """Limpia notificaciones antiguas leídas."""
        return await self.notificacion_repo.delete_antiguas(dias)

    # Métodos privados para envío por canal
    async def _enviar_email(self, notificacion: Notificacion) -> bool:
        """Envía notificación por email."""
        # TODO: Implementar integración con servicio de email
        logger.info(f"Enviando email para notificación {notificacion.id}")
        return True

    async def _enviar_push(self, notificacion: Notificacion) -> bool:
        """Envía notificación push."""
        # TODO: Implementar integración con servicio push
        logger.info(f"Enviando push para notificación {notificacion.id}")
        return True

    async def _enviar_sms(self, notificacion: Notificacion) -> bool:
        """Envía notificación por SMS."""
        # TODO: Implementar integración con servicio SMS
        logger.info(f"Enviando SMS para notificación {notificacion.id}")
        return True


class PreferenciaService:
    """Servicio para gestionar preferencias de notificaciones."""

    def __init__(self, preferencia_repo: PreferenciaNotificacionRepository):
        self.preferencia_repo = preferencia_repo

    async def obtener_preferencias(self, usuario_id: int) -> PreferenciaNotificacion:
        """Obtiene las preferencias de un usuario."""
        return await self.preferencia_repo.get_or_create(usuario_id)

    async def actualizar_preferencias(
        self,
        usuario_id: int,
        in_app_habilitado: Optional[bool] = None,
        email_habilitado: Optional[bool] = None,
        push_habilitado: Optional[bool] = None,
        sms_habilitado: Optional[bool] = None,
        fallas_habilitado: Optional[bool] = None,
        mantenimiento_habilitado: Optional[bool] = None,
        sensores_habilitado: Optional[bool] = None,
        sistema_habilitado: Optional[bool] = None,
        marketing_habilitado: Optional[bool] = None,
        no_molestar_inicio: Optional[str] = None,
        no_molestar_fin: Optional[str] = None,
        configuracion_adicional: Optional[Dict[str, Any]] = None
    ) -> PreferenciaNotificacion:
        """Actualiza las preferencias de un usuario."""
        preferencia = await self.preferencia_repo.get_or_create(usuario_id)
        
        # Actualizar canales
        if in_app_habilitado is not None:
            preferencia.in_app_habilitado = in_app_habilitado
        if email_habilitado is not None:
            preferencia.email_habilitado = email_habilitado
        if push_habilitado is not None:
            preferencia.push_habilitado = push_habilitado
        if sms_habilitado is not None:
            preferencia.sms_habilitado = sms_habilitado
        
        # Actualizar tipos
        if fallas_habilitado is not None:
            preferencia.fallas_habilitado = fallas_habilitado
        if mantenimiento_habilitado is not None:
            preferencia.mantenimiento_habilitado = mantenimiento_habilitado
        if sensores_habilitado is not None:
            preferencia.sensores_habilitado = sensores_habilitado
        if sistema_habilitado is not None:
            preferencia.sistema_habilitado = sistema_habilitado
        if marketing_habilitado is not None:
            preferencia.marketing_habilitado = marketing_habilitado
        
        # Actualizar horarios
        if no_molestar_inicio is not None:
            preferencia.no_molestar_inicio = no_molestar_inicio
        if no_molestar_fin is not None:
            preferencia.no_molestar_fin = no_molestar_fin
        
        # Actualizar configuración adicional
        if configuracion_adicional is not None:
            if preferencia.configuracion_adicional is None:
                preferencia.configuracion_adicional = {}
            preferencia.configuracion_adicional.update(configuracion_adicional)
        
        return await self.preferencia_repo.update(preferencia)
