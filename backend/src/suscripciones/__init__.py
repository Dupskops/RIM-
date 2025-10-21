"""
Módulo de gestión de suscripciones (Freemium/Premium).
"""
from .models import Suscripcion, PlanType, SuscripcionStatus
from .schemas import (
    CreateSuscripcionRequest,
    UpdateSuscripcionRequest,
    UpgradeToPremiumRequest,
    CancelSuscripcionRequest,
    RenewSuscripcionRequest,
    #SearchSuscripcionesRequest,
    SuscripcionResponse,
    #SuscripcionListResponse,
    SuscripcionStatsResponse,
    #MessageResponse
)
from .repositories import SuscripcionRepository
from .services import SuscripcionService
from .events import (
    SuscripcionCreatedEvent,
    SuscripcionUpgradedEvent,
    SuscripcionCancelledEvent,
    SuscripcionRenewedEvent,
    SuscripcionExpiredEvent,
    SuscripcionUpdatedEvent,
    emit_suscripcion_created,
    emit_suscripcion_upgraded,
    emit_suscripcion_cancelled,
    emit_suscripcion_renewed,
    emit_suscripcion_expired,
    emit_suscripcion_updated
)
from .use_cases import (
    CreateSuscripcionUseCase,
    GetSuscripcionUseCase,
    GetActiveSuscripcionUseCase,
    ListSuscripcionesUseCase,
    UpgradeToPremiumUseCase,
    CancelSuscripcionUseCase,
    RenewSuscripcionUseCase,
    GetSuscripcionStatsUseCase
)
from .routes import router as suscripciones_router
from . import event_handlers  # Importar para que esté disponible en main.py


__all__ = [
    # Models
    "Suscripcion",
    "PlanType",
    "SuscripcionStatus",
    
    # Schemas
    "CreateSuscripcionRequest",
    "UpdateSuscripcionRequest",
    "UpgradeToPremiumRequest",
    "CancelSuscripcionRequest",
    "RenewSuscripcionRequest",
    #"SearchSuscripcionesRequest",
    "SuscripcionResponse",
    #"SuscripcionListResponse",
    "SuscripcionStatsResponse",
    #"MessageResponse",
    
    # Repository
    "SuscripcionRepository",
    
    # Services
    "SuscripcionService",
    
    # Events
    "SuscripcionCreatedEvent",
    "SuscripcionUpgradedEvent",
    "SuscripcionCancelledEvent",
    "SuscripcionRenewedEvent",
    "SuscripcionExpiredEvent",
    "SuscripcionUpdatedEvent",
    "emit_suscripcion_created",
    "emit_suscripcion_upgraded",
    "emit_suscripcion_cancelled",
    "emit_suscripcion_renewed",
    "emit_suscripcion_expired",
    "emit_suscripcion_updated",
    
    # Use Cases
    "CreateSuscripcionUseCase",
    "GetSuscripcionUseCase",
    "GetActiveSuscripcionUseCase",
    "ListSuscripcionesUseCase",
    "UpgradeToPremiumUseCase",
    "CancelSuscripcionUseCase",
    "RenewSuscripcionUseCase",
    "GetSuscripcionStatsUseCase",
    
    # Router
    "suscripciones_router",
]
