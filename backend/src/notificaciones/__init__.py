"""
Módulo de notificaciones.
"""
from src.notificaciones.routes import router as notificaciones_router
from src.notificaciones.models import (
    Notificacion,
    PreferenciaNotificacion,
    TipoNotificacion,
    CanalNotificacion,
    EstadoNotificacion
)
from src.notificaciones.schemas import (
    NotificacionCreate,
    NotificacionResponse,
    #NotificacionListResponse,
    NotificacionStatsResponse,
    NotificacionMasivaCreate,
    NotificacionMasivaResponse,
    MarcarLeidaRequest,
    PreferenciaNotificacionUpdate,
    PreferenciaNotificacionResponse,
    WSNotificacionNueva,
    WSNotificacionLeida,
    WSNotificacionesStats
)
from src.notificaciones.events import (
    NotificacionCreadaEvent,
    NotificacionEnviadaEvent,
    NotificacionLeidaEvent,
    NotificacionFallidaEvent,
    PreferenciasActualizadasEvent,
    NotificacionMasivaEvent
)

__all__ = [
    # Router
    "notificaciones_router",
    
    # Models
    "Notificacion",
    "PreferenciaNotificacion",
    "TipoNotificacion",
    "CanalNotificacion",
    "EstadoNotificacion",
    
    # Schemas
    "NotificacionCreate",
    "NotificacionResponse",
    #"NotificacionListResponse",
    "NotificacionStatsResponse",
    "NotificacionMasivaCreate",
    "NotificacionMasivaResponse",
    "MarcarLeidaRequest",
    "PreferenciaNotificacionUpdate",
    "PreferenciaNotificacionResponse",
    "WSNotificacionNueva",
    "WSNotificacionLeida",
    "WSNotificacionesStats",
    
    # Events
    "NotificacionCreadaEvent",
    "NotificacionEnviadaEvent",
    "NotificacionLeidaEvent",
    "NotificacionFallidaEvent",
    "PreferenciasActualizadasEvent",
    "NotificacionMasivaEvent",
]
