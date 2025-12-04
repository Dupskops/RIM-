"""
Rutas API para el módulo de notificaciones.
"""
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.auth.models import Usuario
from src.config.dependencies import get_current_user
from src.shared.base_models import (
    ApiResponse,
    SuccessResponse,
    PaginatedResponse,
    PaginationParams,
    create_paginated_response
)
from src.notificaciones.schemas import (
    NotificacionCreate,
    NotificacionResponse,
    NotificacionStatsResponse,
    NotificacionMasivaCreate,
    NotificacionMasivaResponse,
    NotificacionFilterParams,
    MarcarLeidaRequest,
    PreferenciaNotificacionUpdate,
    PreferenciaNotificacionResponse
)
from src.notificaciones.repositories import (
    NotificacionRepository,
    PreferenciaNotificacionRepository
)
from src.notificaciones.services import (
    NotificacionService,
    PreferenciaService
)
from src.notificaciones.use_cases import (
    CrearNotificacionUseCase,
    CrearNotificacionMasivaUseCase,
    ObtenerNotificacionesUseCase,
    MarcarLeidasUseCase,
    ObtenerEstadisticasUseCase,
    EliminarNotificacionUseCase,
    ObtenerPreferenciasUseCase,
    ActualizarPreferenciasUseCase
)
from src.shared.event_bus import event_bus, get_event_bus
#Import del connection_manager
from src.shared.websocket import (connection_manager) 
from src.notificaciones.models import TipoNotificacion, CanalNotificacion

router = APIRouter()


# Dependencias
def get_notificacion_service(
    session: AsyncSession = Depends(get_db)
) -> NotificacionService:
    """Obtiene el servicio de notificaciones."""
    notificacion_repo = NotificacionRepository(session)
    preferencia_repo = PreferenciaNotificacionRepository(session)
    return NotificacionService(notificacion_repo, preferencia_repo)


def get_preferencia_service(
    session: AsyncSession = Depends(get_db)
) -> PreferenciaService:
    """Obtiene el servicio de preferencias."""
    preferencia_repo = PreferenciaNotificacionRepository(session)
    return PreferenciaService(preferencia_repo)


# Endpoints
@router.post("", response_model=ApiResponse[NotificacionResponse], status_code=status.HTTP_201_CREATED)
async def crear_notificacion(
    data: NotificacionCreate,
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service),
    event_bus = Depends(get_event_bus)
):
    """Crea una nueva notificación."""
    use_case = CrearNotificacionUseCase(service, event_bus)
    
    notificacion = await use_case.execute(
        usuario_id=data.usuario_id,
        titulo=data.titulo,
        mensaje=data.mensaje,
        tipo=data.tipo,
        canal=data.canal,
        referencia_tipo=data.referencia_tipo,
        referencia_id=data.referencia_id
    )
    #Para que llegue la notificacion
    try:
        await connection_manager.broadcast_json({
            "type":"nueva_notificacion",
            "data":{
                "id":notificacion.id,
                "usuario_id": notificacion.usuario_id,
                "titulo": notificacion.titulo,
                "mensaje": notificacion.mensaje,
                "tipo": notificacion.tipo,
                "canal": notificacion.canal

            }

        })
    except Exception as e:
        print(f"⚠️ Error al enviar notificación por WebSocket: {e}")
        

    return ApiResponse(
        success=True,
        message="Notificación creada exitosamente",
        data=NotificacionResponse.model_validate(notificacion)
    )


@router.post("/masiva", response_model=ApiResponse[NotificacionMasivaResponse])
async def crear_notificacion_masiva(
    data: NotificacionMasivaCreate,
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service),
    event_bus = Depends(get_event_bus)
):
    """Crea notificaciones para múltiples usuarios."""
    use_case = CrearNotificacionMasivaUseCase(service, event_bus)
    
    notificaciones = await use_case.execute(
        usuarios_ids=data.usuarios_ids,
        titulo=data.titulo,
        mensaje=data.mensaje,
        tipo=data.tipo,
        canal=data.canal
    )
    
    return ApiResponse(
        success=True,
        message=f"{len(notificaciones)} notificaciones creadas exitosamente",
        data=NotificacionMasivaResponse(
            total_creadas=len(notificaciones),
            notificaciones=[
                NotificacionResponse.model_validate(n) for n in notificaciones
            ]
        )
    )

#Ruta para generar notifiaciones 
@router.post("/seed-demo", response_model=SuccessResponse[None])
async def seed_demo_notificaciones(
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service),
    event_bus = Depends(get_event_bus),
):
    """
    Crea un lote de notificaciones 'previas' para el usuario logueado.
    La idea es que el frontend las vaya consumiendo poco a poco.
    """

    use_case = CrearNotificacionUseCase(service, event_bus)

    notificaciones_demo = [
        {
            "titulo": "Bienvenido a RIM",
            "mensaje": "Este es tu centro de notificaciones. Aquí verás alertas y recomendaciones para tu moto.",
            "tipo": TipoNotificacion.INFO,
        },
        {
            "titulo": "Revisión preventiva recomendada",
            "mensaje": "Tu moto ha superado los 4,500 km desde el último mantenimiento. Revisa frenos y llantas.",
            "tipo": TipoNotificacion.WARNING,
        },
        {
            "titulo": "Chequeo de sensores",
            "mensaje": "Hemos detectado pequeñas variaciones en la temperatura del motor. Te recomendamos un diagnóstico.",
            "tipo": TipoNotificacion.ALERT,
        },
        {
            "titulo": "Todo en orden",
            "mensaje": "En las últimas 24 horas no se han detectado fallas críticas en tu moto.",
            "tipo": TipoNotificacion.SUCCESS,
        },
    ]

    for item in notificaciones_demo:
        # Se crean como notificación IN_APP
        await use_case.execute(
            usuario_id=usuario.id,
            titulo=item["titulo"],
            mensaje=item["mensaje"],
            tipo=item["tipo"],
            canal=CanalNotificacion.IN_APP,
            referencia_tipo=None,
            referencia_id=None,
        )
        # Ojo: aquí NO hacemos broadcast WebSocket, para que tu componente
        # que consulta cada 30s las vaya sacando de la BD.

    return SuccessResponse(
        success=True,
        message="Notificaciones demo creadas correctamente.",
        data=None,
    )



@router.get("", response_model=PaginatedResponse[NotificacionResponse])
async def obtener_notificaciones(
    filters: Annotated[NotificacionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service)
):
    """Obtiene notificaciones del usuario actual."""
    use_case = ObtenerNotificacionesUseCase(service)
    
    notificaciones, total = await use_case.execute(
        usuario_id=usuario.id,
        filters=filters,
        pagination=pagination
    )
    
    return create_paginated_response(
        message="Notificaciones obtenidas exitosamente",
        data=[NotificacionResponse.model_validate(n) for n in notificaciones],
        page=pagination.page,
        per_page=pagination.per_page,
        total_items=total
    )


@router.get("/{notificacion_id}", response_model=ApiResponse[NotificacionResponse])
async def obtener_notificacion(
    notificacion_id: int,
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service)
):
    """Obtiene una notificación específica."""
    notificacion = await service.notificacion_repo.get_by_id(notificacion_id)
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    # Verificar que pertenece al usuario
    if notificacion.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para acceder a esta notificación"
        )
    
    return ApiResponse(
        success=True,
        message="Notificación obtenida exitosamente",
        data=NotificacionResponse.model_validate(notificacion)
    )


@router.patch("/leer", response_model=SuccessResponse[None])
async def marcar_como_leidas(
    data: MarcarLeidaRequest,
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service),
    event_bus = Depends(get_event_bus)
):
    """Marca notificaciones como leídas."""
    use_case = MarcarLeidasUseCase(service, event_bus)
    
    count = await use_case.execute(
        usuario_id=usuario.id,
        notificacion_ids=data.notificacion_ids
    )
    
    return SuccessResponse(
        message=f"{count} notificaciones marcadas como leídas",
        data=None
    )


@router.delete("/{notificacion_id}", response_model=SuccessResponse[None])
async def eliminar_notificacion(
    notificacion_id: int,
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service)
):
    """Elimina una notificación."""
    # Verificar que existe y pertenece al usuario
    notificacion = await service.notificacion_repo.get_by_id(notificacion_id)
    
    if not notificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada"
        )
    
    if notificacion.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para eliminar esta notificación"
        )
    
    use_case = EliminarNotificacionUseCase(service)
    await use_case.execute(notificacion_id)
    
    return SuccessResponse(
        message="Notificación eliminada exitosamente",
        data=None
    )


@router.get("/stats", response_model=ApiResponse[NotificacionStatsResponse])
async def obtener_estadisticas(
    usuario: Usuario = Depends(get_current_user),
    service: NotificacionService = Depends(get_notificacion_service)
):
    """Obtiene estadísticas de notificaciones del usuario."""
    use_case = ObtenerEstadisticasUseCase(service)
    stats = await use_case.execute(usuario.id)
    
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=NotificacionStatsResponse(**stats)
    )


@router.get("/preferencias", response_model=ApiResponse[PreferenciaNotificacionResponse])
async def obtener_preferencias(
    usuario: Usuario = Depends(get_current_user),
    service: PreferenciaService = Depends(get_preferencia_service)
):
    """Obtiene las preferencias de notificaciones del usuario."""
    use_case = ObtenerPreferenciasUseCase(service)
    preferencia = await use_case.execute(usuario.id)
    
    return ApiResponse(
        success=True,
        message="Preferencias obtenidas exitosamente",
        data=PreferenciaNotificacionResponse.model_validate(preferencia)
    )


@router.put("/preferencias", response_model=ApiResponse[PreferenciaNotificacionResponse])
async def actualizar_preferencias(
    data: PreferenciaNotificacionUpdate,
    usuario: Usuario = Depends(get_current_user),
    service: PreferenciaService = Depends(get_preferencia_service),
    event_bus = Depends(get_event_bus)
):
    """Actualiza las preferencias de notificaciones del usuario."""
    use_case = ActualizarPreferenciasUseCase(service, event_bus)
    
    preferencia = await use_case.execute(
        usuario_id=usuario.id,
        in_app_habilitado=data.in_app_habilitado,
        email_habilitado=data.email_habilitado,
        push_habilitado=data.push_habilitado,
        sms_habilitado=data.sms_habilitado,
        fallas_habilitado=data.notif_fallas_habilitado,
        mantenimiento_habilitado=data.notif_mantenimiento_habilitado,
        sensores_habilitado=data.notif_sensores_habilitado,
        sistema_habilitado=data.notif_sistema_habilitado,
        marketing_habilitado=data.notif_marketing_habilitado,
        no_molestar_inicio=data.no_molestar_inicio,
        no_molestar_fin=data.no_molestar_fin,
        configuracion_adicional=data.configuracion_adicional
    )
    
    return ApiResponse(
        success=True,
        message="Preferencias actualizadas exitosamente",
        data=PreferenciaNotificacionResponse.model_validate(preferencia)
    )


