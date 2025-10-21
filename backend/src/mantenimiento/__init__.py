"""
Módulo de mantenimiento.

Este módulo gestiona los mantenimientos programados y correctivos
de las motocicletas conectadas al sistema RIM.
"""
from src.mantenimiento.routes import router as mantenimiento_router
from src.mantenimiento.models import Mantenimiento
from src.mantenimiento.schemas import (
    MantenimientoCreate,
    MantenimientoMLCreate,
    MantenimientoUpdate,
    MantenimientoIniciar,
    MantenimientoCompletar,
    MantenimientoResponse,
    #MantenimientoListResponse,
    MantenimientoStatsResponse,
    MantenimientoHistorialResponse
)
from src.mantenimiento.events import (
    MantenimientoProgramadoEvent,
    MantenimientoUrgenteEvent,
    MantenimientoVencidoEvent,
    MantenimientoIniciadoEvent,
    MantenimientoCompletadoEvent,
    MantenimientoRecomendadoIAEvent,
    AlertaMantenimientoProximoEvent
)

__all__ = [
    # Router
    "mantenimiento_router",
    
    # Models
    "Mantenimiento",
    
    # Schemas
    "MantenimientoCreate",
    "MantenimientoMLCreate",
    "MantenimientoUpdate",
    "MantenimientoIniciar",
    "MantenimientoCompletar",
    "MantenimientoResponse",
    #"MantenimientoListResponse",
    "MantenimientoStatsResponse",
    "MantenimientoHistorialResponse",
    
    # Events
    "MantenimientoProgramadoEvent",
    "MantenimientoUrgenteEvent",
    "MantenimientoVencidoEvent",
    "MantenimientoIniciadoEvent",
    "MantenimientoCompletadoEvent",
    "MantenimientoRecomendadoIAEvent",
    "AlertaMantenimientoProximoEvent",
]
