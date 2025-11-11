"""
Módulo de gestión de suscripciones (Freemium/Premium).
"""
from .models import (
    PeriodoPlan, 
    EstadoSuscripcion, 
    Plan, 
    Caracteristica, 
    PlanCaracteristica, 
    Suscripcion,
)
from .schemas import (
    CaracteristicaReadSchema,
    PlanReadSchema,
    SuscripcionUsuarioReadSchema,
    TransaccionCreateResponse,
    TransaccionReadSchema,
    PaymentNotificationSchema,
    CheckoutCreateRequest,
    SuscripcionCancelRequest,
    AdminAssignSubscriptionRequest,
)
from .repositories import SuscripcionRepository
from .repositories import PlanesRepository
from .services import SuscripcionService
from .events import (
    SuscripcionCreatedEvent,
    PlanChangedEvent,
    SuscripcionCancelledEvent,
    emit_suscripcion_created,
    emit_plan_changed,
    emit_suscripcion_cancelled,
)
from .use_cases import (
    ListPlanesUseCase,
    GetMySuscripcionUseCase,
    CheckLimiteUseCase,
    RegistrarUsoUseCase,
    GetHistorialUsoUseCase,
    CambiarPlanUseCase,
    CancelSuscripcionUseCase,
)
from .routes import router as suscripciones_router
from . import event_handlers  # Importar para que esté disponible en main.py
from .event_handlers import register_event_handlers


__all__ = [
    # Models
    "Suscripcion",
    "PeriodoPlan",
    "EstadoSuscripcion",
    "Plan",
    "Caracteristica",
    "PlanCaracteristica",

    # Schemas
    "CaracteristicaReadSchema",
    "PlanReadSchema",
    "SuscripcionUsuarioReadSchema",
    "TransaccionCreateResponse",
    "TransaccionReadSchema",
    "PaymentNotificationSchema",
    "CheckoutCreateRequest",
    "SuscripcionCancelRequest",
    "AdminAssignSubscriptionRequest",

    # Repository
    "SuscripcionRepository",
    "PlanesRepository",
    
    # Services
    "SuscripcionService",
    
    # Events (v2.3 Freemium)
    "SuscripcionCreatedEvent",
    "PlanChangedEvent",
    "SuscripcionCancelledEvent",
    "emit_suscripcion_created",
    "emit_plan_changed",
    "emit_suscripcion_cancelled",

    # Event handlers
    "register_event_handlers",
    
    # Use Cases (v2.3 Freemium)
    "ListPlanesUseCase",
    "GetMySuscripcionUseCase",
    "CheckLimiteUseCase",
    "RegistrarUsoUseCase",
    "GetHistorialUsoUseCase",
    "CambiarPlanUseCase",
    "CancelSuscripcionUseCase",

    # Router
    "suscripciones_router",

    "event_handlers"
]
