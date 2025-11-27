"""
Módulo de gestión de fallas de motos.
Detecta, diagnostica y resuelve anomalías en las motos.

MVP v2.3 - Alineado con CREATE_TABLES_MVP_V2.2.sql

Cambios v2.3:
- Eliminados: campos ML (confianza_ml, modelo_ml_usado, prediccion_ml)
- Eliminados: campos diagnóstico (fecha_diagnostico, costo_estimado, costo_real, solucion_aplicada, notas_tecnico)
- Agregado: componente_id (requerido)
- Estados simplificados: DETECTADA → EN_REPARACION → RESUELTA
- Tipo de falla ahora es string libre (no ENUM)
"""

from .routes import router as fallas_router
from .models import Falla, SeveridadFalla, EstadoFalla, OrigenDeteccion
from .schemas import (
    FallaCreate,
    FallaUpdate,
    FallaResponse,
    FallaListResponse,
    FallaStatsResponse,
    FallaFilterParams
)
from .events import (
    FallaDetectadaEvent,
    FallaActualizadaEvent,
    FallaResueltaEvent
)
from .use_cases import (
    CreateFallaUseCase,
    GetFallaByIdUseCase,
    GetFallaByCodigoUseCase,
    ListFallasByMotoUseCase,
    UpdateFallaUseCase,
    DiagnosticarFallaUseCase,
    ResolverFallaUseCase,
    GetFallaStatsUseCase,
    AutoResolveFallasUseCase
)
from .repositories import FallaRepository
from .validators import validate_falla_data, validate_transition_estado

__all__ = [
    # Router
    "fallas_router",
    
    # Models
    "Falla",
    "SeveridadFalla",
    "EstadoFalla",
    "OrigenDeteccion",
    
    # Schemas
    "FallaCreate",
    "FallaUpdate",
    "FallaResponse",
    "FallaListResponse",
    "FallaStatsResponse",
    "FallaFilterParams",
    
    # Events
    "FallaDetectadaEvent",
    "FallaActualizadaEvent",
    "FallaResueltaEvent",
    
    # Use Cases
    "CreateFallaUseCase",
    "GetFallaByIdUseCase",
    "GetFallaByCodigoUseCase",
    "ListFallasByMotoUseCase",
    "UpdateFallaUseCase",
    "DiagnosticarFallaUseCase",
    "ResolverFallaUseCase",
    "GetFallaStatsUseCase",
    "AutoResolveFallasUseCase",
    
    # Repository
    "FallaRepository",
    
    # Validators
    "validate_falla_data",
    "validate_transition_estado",
]
