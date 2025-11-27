"""
Módulo de sensores y telemetría.

Gestión completa de sensores IoT para motos:
- Templates: Plantillas de sensores predefinidas por modelo
- Sensors: Instancias de sensores asociadas a motos
- Lecturas: Telemetría en tiempo real
- Componentes: Estados agregados de componentes físicos
- Provisión: Auto-provisión basada en modelo de moto

Arquitectura:
- REST API: Endpoints síncronos para CRUD
- WebSocket: Telemetría en tiempo real con rooms
- Events: Eventos de dominio para integración con otros módulos
- Use Cases: Orquestación de lógica de negocio

Flujos principales:
1. Provisión: modelo → templates → componentes + sensores
2. Telemetría: WebSocket → lectura → validación → eventos → broadcast
3. Agregación: sensor_states → component_state → alertas
"""

# Models
from .models import (
    SensorState,
    SensorTemplate,
    Sensor,
    Lectura
)

# Schemas
from .schemas import (
    SensorTemplateCreate,
    SensorTemplateUpdate,
    SensorTemplateRead,
    CreateSensorRequest,
    UpdateSensorRequest,
    SensorRead,
    CreateLecturaRequest,
    LecturaRead,
    SensorStatsResponse,
    ComponentStateResponse
)

# Events
from .events import (
    SensorRegisteredEvent,
    LecturaRegistradaEvent,
    ComponenteEstadoActualizadoEvent,
    AlertaSensorEvent,
    PrediccionGeneradaEvent,
    emit_sensor_registered,
    emit_lectura_registrada,
    emit_componente_estado_actualizado,
    emit_alerta_sensor,
    emit_prediccion_generada
)

# Repositories
from .repositories import (
    SensorTemplateRepository,
    SensorRepository,
    LecturaRepository,
    MotoComponenteRepository
)

# Services
from .services import SensorService

# Use Cases
from .use_cases import (
    CreateSensorTemplateUseCase,
    GetSensorTemplateUseCase,
    CreateSensorUseCase,
    UpdateSensorUseCase,
    CreateLecturaUseCase,
    ProvisionSensorsUseCase,
    UpdateComponentStateUseCase,
    GetSensorStatsUseCase
)

# Routes
from .routes import router as sensores_router

# WebSocket
from .websocket import router as websocket_router, manager as ws_manager

__all__ = [
    # Models
    "SensorState",
    "SensorTemplate",
    "Sensor",
    "Lectura",
    
    # Schemas
    "SensorTemplateCreate",
    "SensorTemplateUpdate",
    "SensorTemplateRead",
    "CreateSensorRequest",
    "UpdateSensorRequest",
    "SensorRead",
    "CreateLecturaRequest",
    "LecturaRead",
    "SensorStatsResponse",
    "ComponentStateResponse",
    
    # Events
    "SensorRegisteredEvent",
    "LecturaRegistradaEvent",
    "ComponenteEstadoActualizadoEvent",
    "AlertaSensorEvent",
    "PrediccionGeneradaEvent",
    "emit_sensor_registered",
    "emit_lectura_registrada",
    "emit_componente_estado_actualizado",
    "emit_alerta_sensor",
    "emit_prediccion_generada",
    
    # Repositories
    "SensorTemplateRepository",
    "SensorRepository",
    "LecturaRepository",
    "MotoComponenteRepository",
    
    # Services
    "SensorService",
    
    # Use Cases
    "CreateSensorTemplateUseCase",
    "GetSensorTemplateUseCase",
    "CreateSensorUseCase",
    "UpdateSensorUseCase",
    "CreateLecturaUseCase",
    "ProvisionSensorsUseCase",
    "UpdateComponentStateUseCase",
    "GetSensorStatsUseCase",
    
    # Routes & WebSocket
    "sensores_router",
    "websocket_router",
    "ws_manager"
]
