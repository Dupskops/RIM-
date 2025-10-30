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
    ListPlanesUseCase,
    CheckoutCreateUseCase,
    ProcessPaymentNotificationUseCase,
    CancelSuscripcionUseCase,
    AdminAssignSubscriptionUseCase,
    TransaccionListUseCase,
)
from .routes import router as suscripciones_router
from . import event_handlers  # Importar para que esté disponible en main.py
from .event_handlers import register_event_handlers

from .events import (
    TransaccionCreatedEvent,
    TransaccionUpdatedEvent,
    SuscripcionActualizadaEvent,
    emit_transaccion_creada,
    emit_transaccion_actualizada,
    emit_suscripcion_actualizada,
)


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
    # Transaccion events
    "TransaccionCreatedEvent",
    "TransaccionUpdatedEvent",
    "SuscripcionActualizadaEvent",
    "emit_transaccion_creada",
    "emit_transaccion_actualizada",
    "emit_suscripcion_actualizada",

    # Event handlers
    "register_event_handlers",
    
    # Use Cases
    "ListPlanesUseCase",
    "CheckoutCreateUseCase",
    "ProcessPaymentNotificationUseCase",
    "CancelSuscripcionUseCase",
    "AdminAssignSubscriptionUseCase",
    "TransaccionListUseCase",

    # Router
    "suscripciones_router",

    "event_handlers"
]
