"""
Módulo de Machine Learning (ML).

Predicción de fallas y detección de anomalías usando modelos entrenados.
"""
from src.ml.routes import router as ml_router
from src.ml.models import Prediccion, EntrenamientoModelo
from src.ml.schemas import (
    PrediccionFallaRequest,
    PrediccionAnomaliaRequest,
    PrediccionResponse,
    PrediccionValidacionRequest,
    ModeloInfoResponse,
    EstadisticasPrediccionesResponse
)
from src.ml.events import (
    PrediccionGeneradaEvent,
    PrediccionConfirmadaEvent,
    PrediccionFalsaEvent,
    AnomaliaDetectadaEvent,
    ModeloActualizadoEvent,
    EntrenamientoFinalizadoEvent
)

__all__ = [
    # Router
    "ml_router",
    
    # Models
    "Prediccion",
    "EntrenamientoModelo",
    
    # Schemas
    "PrediccionFallaRequest",
    "PrediccionAnomaliaRequest",
    "PrediccionResponse",
    "PrediccionValidacionRequest",
    "ModeloInfoResponse",
    "EstadisticasPrediccionesResponse",
    
    # Events
    "PrediccionGeneradaEvent",
    "PrediccionConfirmadaEvent",
    "PrediccionFalsaEvent",
    "AnomaliaDetectadaEvent",
    "ModeloActualizadoEvent",
    "EntrenamientoFinalizadoEvent",
]
