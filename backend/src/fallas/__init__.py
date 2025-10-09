"""
Módulo de gestión de fallas de motos.
Detecta, diagnostica y resuelve anomalías en las motos.
"""

from .routes import router as fallas_router
from .models import Falla
from .schemas import (
    FallaCreate,
    FallaMLCreate,
    FallaUpdate,
    FallaDiagnosticar,
    FallaResolver,
    FallaResponse,
    FallaListResponse,
    FallaStatsResponse,
    FallaPredictionResponse
)
from .events import (
    FallaDetectadaEvent,
    FallaCriticaEvent,
    FallaDiagnosticadaEvent,
    FallaResueltaEvent,
    FallaMLPredictedEvent
)

__all__ = [
    # Router
    "fallas_router",
    
    # Models
    "Falla",
    
    # Schemas
    "FallaCreate",
    "FallaMLCreate",
    "FallaUpdate",
    "FallaDiagnosticar",
    "FallaResolver",
    "FallaResponse",
    "FallaListResponse",
    "FallaStatsResponse",
    "FallaPredictionResponse",
    
    # Events
    "FallaDetectadaEvent",
    "FallaCriticaEvent",
    "FallaDiagnosticadaEvent",
    "FallaResueltaEvent",
    "FallaMLPredictedEvent",
]
