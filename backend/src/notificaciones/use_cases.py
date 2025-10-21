"""
Casos de uso para el módulo de notificaciones.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from src.shared.base_models import PaginationParams
from src.notificaciones.models import (
    Notificacion,
    PreferenciaNotificacion,
    CanalNotificacion,
    TipoNotificacion
)
from src.notificaciones.schemas import NotificacionFilterParams
from src.notificaciones.services import NotificacionService, PreferenciaService
from src.notificaciones.events import (
    NotificacionCreadaEvent,
    NotificacionEnviadaEvent,
    NotificacionLeidaEvent,
    NotificacionFallidaEvent,
    PreferenciasActualizadasEvent,
    NotificacionMasivaEvent
)
from src.shared.event_bus import EventBus


class CrearNotificacionUseCase:
    """Caso de uso para crear una notificación."""

    def __init__(
        self,
        notificacion_service: NotificacionService,
        event_bus: EventBus
    ):
        self.notificacion_service = notificacion_service
        self.event_bus = event_bus

    async def execute(
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
        # Crear notificación
        notificacion = await self.notificacion_service.crear_notificacion(
            usuario_id=usuario_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            canal=canal,
            datos_adicionales=datos_adicionales,
            accion_url=accion_url,
            accion_tipo=accion_tipo,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            expira_en=expira_en
        )
        
        # Emitir evento
        await self.event_bus.publish(
            NotificacionCreadaEvent(
                notificacion_id=notificacion.id,
                usuario_id=notificacion.usuario_id,
                tipo=notificacion.tipo,
                canal=notificacion.canal,
                titulo=notificacion.titulo
            )
        )
        
        return notificacion


class CrearNotificacionMasivaUseCase:
    """Caso de uso para crear notificaciones masivas."""

    def __init__(
        self,
        notificacion_service: NotificacionService,
        event_bus: EventBus
    ):
        self.notificacion_service = notificacion_service
        self.event_bus = event_bus

    async def execute(
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
        # Crear notificaciones
        notificaciones = await self.notificacion_service.crear_notificaciones_masivas(
            usuarios_ids=usuarios_ids,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            canal=canal,
            datos_adicionales=datos_adicionales,
            accion_url=accion_url,
            accion_tipo=accion_tipo,
            expira_en=expira_en
        )
        
        # Emitir evento
        await self.event_bus.publish(
            NotificacionMasivaEvent(
                titulo=titulo,
                total_usuarios=len(usuarios_ids),
                canal=canal,
                tipo=tipo
            )
        )
        
        # Emitir eventos individuales
        for notif in notificaciones:
            await self.event_bus.publish(
                NotificacionCreadaEvent(
                    notificacion_id=notif.id,
                    usuario_id=notif.usuario_id,
                    tipo=notif.tipo,
                    canal=notif.canal,
                    titulo=notif.titulo
                )
            )
        
        return notificaciones


class EnviarNotificacionUseCase:
    """Caso de uso para enviar una notificación."""

    def __init__(
        self,
        notificacion_service: NotificacionService,
        event_bus: EventBus
    ):
        self.notificacion_service = notificacion_service
        self.event_bus = event_bus

    async def execute(self, notificacion_id: int) -> bool:
        """Envía una notificación."""
        # Obtener notificación antes de enviar
        notificacion = await self.notificacion_service.notificacion_repo.get_by_id(
            notificacion_id
        )
        if not notificacion:
            return False
        
        # Enviar
        exito = await self.notificacion_service.enviar_notificacion(notificacion_id)
        
        # Emitir evento apropiado
        if exito:
            await self.event_bus.publish(
                NotificacionEnviadaEvent(
                    notificacion_id=notificacion.id,
                    usuario_id=notificacion.usuario_id,
                    canal=notificacion.canal,
                    enviada_en=datetime.now()
                )
            )
        else:
            await self.event_bus.publish(
                NotificacionFallidaEvent(
                    notificacion_id=notificacion.id,
                    usuario_id=notificacion.usuario_id,
                    canal=notificacion.canal,
                    error="Error al enviar",
                    intentos=notificacion.intentos_envio
                )
            )
        
        return exito


class MarcarLeidasUseCase:
    """Caso de uso para marcar notificaciones como leídas."""

    def __init__(
        self,
        notificacion_service: NotificacionService,
        event_bus: EventBus
    ):
        self.notificacion_service = notificacion_service
        self.event_bus = event_bus

    async def execute(
        self,
        usuario_id: int,
        notificacion_ids: Optional[List[int]] = None
    ) -> int:
        """Marca notificaciones como leídas."""
        if notificacion_ids:
            # Marcar notificaciones específicas
            count = await self.notificacion_service.marcar_varias_como_leidas(
                notificacion_ids
            )
            
            # Emitir eventos
            for notif_id in notificacion_ids:
                await self.event_bus.publish(
                    NotificacionLeidaEvent(
                        notificacion_id=notif_id,
                        usuario_id=usuario_id,
                        leida_en=datetime.now()
                    )
                )
        else:
            # Marcar todas
            count = await self.notificacion_service.marcar_todas_como_leidas(
                usuario_id
            )
        
        return count


class ObtenerNotificacionesUseCase:
    """Caso de uso para obtener notificaciones."""

    def __init__(self, notificacion_service: NotificacionService):
        self.notificacion_service = notificacion_service

    async def execute(
        self,
        usuario_id: int,
        filters: NotificacionFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Notificacion], int]:
        """Obtiene notificaciones de un usuario con filtros y paginación."""
        return await self.notificacion_service.obtener_notificaciones(
            usuario_id=usuario_id,
            solo_no_leidas=filters.solo_no_leidas,
            skip=pagination.offset,
            limit=pagination.limit
        )


class ObtenerEstadisticasUseCase:
    """Caso de uso para obtener estadísticas."""

    def __init__(self, notificacion_service: NotificacionService):
        self.notificacion_service = notificacion_service

    async def execute(self, usuario_id: int) -> Dict[str, Any]:
        """Obtiene estadísticas de notificaciones."""
        return await self.notificacion_service.obtener_estadisticas(usuario_id)


class EliminarNotificacionUseCase:
    """Caso de uso para eliminar una notificación."""

    def __init__(self, notificacion_service: NotificacionService):
        self.notificacion_service = notificacion_service

    async def execute(self, notificacion_id: int) -> bool:
        """Elimina una notificación."""
        return await self.notificacion_service.eliminar_notificacion(notificacion_id)


class ObtenerPreferenciasUseCase:
    """Caso de uso para obtener preferencias."""

    def __init__(self, preferencia_service: PreferenciaService):
        self.preferencia_service = preferencia_service

    async def execute(self, usuario_id: int) -> PreferenciaNotificacion:
        """Obtiene preferencias de un usuario."""
        return await self.preferencia_service.obtener_preferencias(usuario_id)


class ActualizarPreferenciasUseCase:
    """Caso de uso para actualizar preferencias."""

    def __init__(
        self,
        preferencia_service: PreferenciaService,
        event_bus: EventBus
    ):
        self.preferencia_service = preferencia_service
        self.event_bus = event_bus

    async def execute(
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
        """Actualiza preferencias de un usuario."""
        # Actualizar
        preferencia = await self.preferencia_service.actualizar_preferencias(
            usuario_id=usuario_id,
            in_app_habilitado=in_app_habilitado,
            email_habilitado=email_habilitado,
            push_habilitado=push_habilitado,
            sms_habilitado=sms_habilitado,
            fallas_habilitado=fallas_habilitado,
            mantenimiento_habilitado=mantenimiento_habilitado,
            sensores_habilitado=sensores_habilitado,
            sistema_habilitado=sistema_habilitado,
            marketing_habilitado=marketing_habilitado,
            no_molestar_inicio=no_molestar_inicio,
            no_molestar_fin=no_molestar_fin,
            configuracion_adicional=configuracion_adicional
        )
        
        # Emitir evento
        await self.event_bus.publish(
            PreferenciasActualizadasEvent(
                usuario_id=usuario_id,
                preferencias={
                    "in_app_habilitado": preferencia.in_app_habilitado,
                    "email_habilitado": preferencia.email_habilitado,
                    "push_habilitado": preferencia.push_habilitado,
                    "sms_habilitado": preferencia.sms_habilitado,
                }
            )
        )
        
        return preferencia


class ProcesarPendientesUseCase:
    """Caso de uso para procesar notificaciones pendientes."""

    def __init__(self, notificacion_service: NotificacionService):
        self.notificacion_service = notificacion_service

    async def execute(self, limite: int = 100) -> int:
        """Procesa notificaciones pendientes."""
        return await self.notificacion_service.procesar_pendientes(limite)


class ReintentarFallidasUseCase:
    """Caso de uso para reintentar notificaciones fallidas."""

    def __init__(self, notificacion_service: NotificacionService):
        self.notificacion_service = notificacion_service

    async def execute(self, limite: int = 50) -> int:
        """Reintenta notificaciones fallidas."""
        return await self.notificacion_service.reintentar_fallidas(limite)
