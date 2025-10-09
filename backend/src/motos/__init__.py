"""
Módulo de gestión de motos KTM.
"""
from .models import Moto
from .schemas import (
    RegisterMotoRequest,
    UpdateMotoRequest,
    UpdateKilometrajeRequest,
    #SearchMotosRequest,
    MotoResponse,
    #MotoListResponse,
    MotoStatsResponse,
    #MessageResponse
)
from .repositories import MotoRepository
from .services import MotoService
from .events import (
    MotoRegisteredEvent,
    MotoUpdatedEvent,
    MotoDeletedEvent,
    KilometrajeUpdatedEvent,
    MotoTransferredEvent,
    emit_moto_registered,
    emit_moto_updated,
    emit_moto_deleted,
    emit_kilometraje_updated,
    emit_moto_transferred
)
from .use_cases import (
    RegisterMotoUseCase,
    GetMotoUseCase,
    ListMotosUseCase,
    UpdateMotoUseCase,
    DeleteMotoUseCase,
    UpdateKilometrajeUseCase,
    GetMotoStatsUseCase
)
from .routes import router as motos_router


__all__ = [
    # Models
    "Moto",
    
    # Schemas
    "RegisterMotoRequest",
    "UpdateMotoRequest",
    "UpdateKilometrajeRequest",
    #"SearchMotosRequest",
    "MotoResponse",
    #"MotoListResponse",
    "MotoStatsResponse",
    #"MessageResponse",
    
    # Repository
    "MotoRepository",
    
    # Services
    "MotoService",
    
    # Events
    "MotoRegisteredEvent",
    "MotoUpdatedEvent",
    "MotoDeletedEvent",
    "KilometrajeUpdatedEvent",
    "MotoTransferredEvent",
    "emit_moto_registered",
    "emit_moto_updated",
    "emit_moto_deleted",
    "emit_kilometraje_updated",
    "emit_moto_transferred",
    
    # Use Cases
    "RegisterMotoUseCase",
    "GetMotoUseCase",
    "ListMotosUseCase",
    "UpdateMotoUseCase",
    "DeleteMotoUseCase",
    "UpdateKilometrajeUseCase",
    "GetMotoStatsUseCase",
    
    # Router
    "motos_router",
]
