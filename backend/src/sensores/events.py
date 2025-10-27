"""
Eventos de dominio para el módulo de sensores.

Arquitectura event-driven:
- SensorRegisteredEvent: Sensor creado (moto, notificaciones)
- LecturaRegistradaEvent: Telemetría persistida (ML, notificaciones)
- ComponenteEstadoActualizadoEvent: Estado agregado cambia (fallas, mantenimiento, notificaciones)
- AlertaSensorEvent: Valor fuera de umbral (fallas, notificaciones)

Todos los eventos incluyen:
- event_id: ID único del evento
- timestamp: Momento de emisión
- correlation_id: Para trazabilidad entre eventos relacionados
- metadata: Contexto adicional
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from src.shared.event_bus import Event


from src.shared.event_bus import Event


# ==================== EVENT CLASSES ====================

@dataclass
class SensorRegisteredEvent(Event):
    """
    Evento emitido cuando se registra un nuevo sensor.
    
    Consumidores:
    - Motos: Actualizar contadores de sensores (opcional)
    - Notificaciones: Informar al usuario (opcional)
    """
    sensor_id: UUID
    moto_id: int  # FK hacia motos (int)
    tipo: str
    template_id: Optional[UUID] = None
    componente_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None
    
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LecturaRegistradaEvent(Event):
    """
    Evento emitido cuando se persiste una lectura de sensor.
    
    Consumidores:
    - ML: Inferencia en tiempo real, acumulación de dataset
    - Notificaciones: Broadcast realtime a WebSocket clients (opcional)
    """
    lectura_id: int
    moto_id: int  # FK hacia motos (int)
    sensor_id: UUID
    component_id: Optional[UUID]
    ts: datetime
    valor: Dict[str, Any]  # {"value": X, "unit": "Y"}
    timestamp: Optional[datetime] = None
    
    correlation_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComponenteEstadoActualizadoEvent(Event):
    """
    Evento emitido cuando cambia el estado agregado de un componente físico.
    
    CRÍTICO: Este evento refleja cambios REALES basados en sensores.
    NO se emite por predicciones ML (esas son informativas).
    
    Consumidores:
    - Fallas: Auto-crear falla si new_state == 'critical'
    - Mantenimiento: Sugerir mantenimiento preventivo si >= 'warning'
    - Notificaciones: Alertas push/email según severidad y plan
    - Chatbot: Contexto para respuestas
    """
    componente_id: UUID
    moto_id: int  # FK hacia motos (int)
    tipo_componente: str
    old_state: str  # ComponentState value
    new_state: str  # ComponentState value
    timestamp: Optional[datetime] = None
    
    # Datos de agregación (para trazabilidad)
    aggregation_data: Dict[str, Any] = field(default_factory=dict)  # {"max_score": X, "sensor_states": {...}}
    sensor_contributions: Dict[UUID, Dict[str, Any]] = field(default_factory=dict)  # {sensor_id: {"state": "ok", "score": 0}}
    
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertaSensorEvent(Event):
    """
    Evento emitido cuando un sensor reporta valor fuera de umbrales.
    
    Consumidores:
    - Fallas: Crear falla si severidad >= 'high'
    - Notificaciones: Alerta inmediata a usuario
    """
    sensor_id: UUID
    moto_id: int  # FK hacia motos (int)
    component_id: Optional[UUID]
    tipo_sensor: str
    
    valor_actual: Dict[str, Any]  # {"value": X, "unit": "Y"}
    umbral_violado: Dict[str, Any]  # {"min": A, "max": B}
    severidad: str  # low, medium, high, critical
    mensaje: str
    timestamp: Optional[datetime] = None
    
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrediccionGeneradaEvent(Event):
    """
    Evento emitido por ML tras inferencia sobre lecturas.
    
    ⚠️ IMPORTANTE: Este evento es INFORMATIVO/PREVENTIVO.
    NO modifica component_state (solo lecturas reales lo hacen).
    
    Consumidores:
    - Notificaciones: Alertas preventivas/contextuales (Premium)
    - Mantenimiento: Sugerencias predictivas
    - Chatbot: Contexto para conversaciones
    
    Producido por: ml.use_cases (escucha LecturaRegistradaEvent)
    """
    moto_id: int  # FK hacia motos (int)
    sensor_id: Optional[UUID]
    component_id: Optional[UUID]
    
    tipo_prediccion: str  # failure_forecast, degradation, anomaly
    confianza: float  # 0.0 - 1.0
    severidad: str  # info, low, medium, high
    details: Dict[str, Any]  # Detalles específicos de la predicción
    suggested_action: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    correlation_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==================== EMIT HELPER FUNCTIONS ====================

async def emit_sensor_registered(
    sensor_id: UUID,
    moto_id: int,
    tipo: str,
    template_id: Optional[UUID] = None,
    componente_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emite evento de sensor registrado.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        tipo: Tipo de sensor
        template_id: ID de la plantilla (opcional)
        componente_id: ID del componente (opcional)
        correlation_id: ID de correlación (opcional)
        metadata: Metadata adicional (opcional)
    """
    event = SensorRegisteredEvent(
        timestamp=datetime.now(timezone.utc),
        sensor_id=sensor_id,
        moto_id=moto_id,
        tipo=tipo,
        template_id=template_id,
        componente_id=componente_id,
        correlation_id=correlation_id,
        metadata=metadata or {}
    )
    await event.emit()


async def emit_lectura_registrada(
    lectura_id: int,
    moto_id: int,
    sensor_id: UUID,
    ts: datetime,
    valor: Dict[str, Any],
    component_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emite evento de lectura registrada.
    
    Args:
        lectura_id: ID de la lectura
        moto_id: ID de la moto
        sensor_id: ID del sensor
        ts: Timestamp de la lectura
        valor: Valor de la lectura (JSONB)
        component_id: ID del componente (opcional)
        correlation_id: ID de correlación (opcional)
        metadata: Metadata adicional (opcional)
    """
    event = LecturaRegistradaEvent(
        timestamp=datetime.now(timezone.utc),
        lectura_id=lectura_id,
        moto_id=moto_id,
        sensor_id=sensor_id,
        component_id=component_id,
        ts=ts,
        valor=valor,
        correlation_id=correlation_id,
        metadata=metadata
    )
    await event.emit()


async def emit_componente_estado_actualizado(
    componente_id: UUID,
    moto_id: int,
    tipo_componente: str,
    old_state: str,
    new_state: str,
    aggregation_data: Optional[Dict[str, Any]] = None,
    sensor_contributions: Optional[Dict[UUID, Dict[str, Any]]] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emite evento de estado de componente actualizado.
    
    Args:
        componente_id: ID del componente
        moto_id: ID de la moto
        tipo_componente: Tipo de componente
        old_state: Estado anterior
        new_state: Nuevo estado
        aggregation_data: Datos de agregación (opcional)
        sensor_contributions: Contribuciones de sensores (opcional)
        correlation_id: ID de correlación (opcional)
        metadata: Metadata adicional (opcional)
    """
    event = ComponenteEstadoActualizadoEvent(
        timestamp=datetime.now(timezone.utc),
        componente_id=componente_id,
        moto_id=moto_id,
        tipo_componente=tipo_componente,
        old_state=old_state,
        new_state=new_state,
        aggregation_data=aggregation_data or {},
        sensor_contributions=sensor_contributions or {},
        correlation_id=correlation_id,
        metadata=metadata or {}
    )
    await event.emit()


async def emit_alerta_sensor(
    sensor_id: UUID,
    moto_id: int,
    tipo_sensor: str,
    valor_actual: Dict[str, Any],
    umbral_violado: Dict[str, Any],
    severidad: str,
    mensaje: str,
    component_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emite evento de alerta de sensor.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        tipo_sensor: Tipo de sensor
        valor_actual: Valor actual (JSONB)
        umbral_violado: Umbral violado (JSONB)
        severidad: Severidad de la alerta
        mensaje: Mensaje de la alerta
        component_id: ID del componente (opcional)
        correlation_id: ID de correlación (opcional)
        metadata: Metadata adicional (opcional)
    """
    event = AlertaSensorEvent(
        timestamp=datetime.now(timezone.utc),
        sensor_id=sensor_id,
        moto_id=moto_id,
        component_id=component_id,
        tipo_sensor=tipo_sensor,
        valor_actual=valor_actual,
        umbral_violado=umbral_violado,
        severidad=severidad,
        mensaje=mensaje,
        correlation_id=correlation_id,
        metadata=metadata or {}
    )
    await event.emit()


async def emit_prediccion_generada(
    moto_id: int,
    tipo_prediccion: str,
    confianza: float,
    severidad: str,
    details: Dict[str, Any],
    sensor_id: Optional[UUID] = None,
    component_id: Optional[UUID] = None,
    suggested_action: Optional[str] = None,
    correlation_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Emite evento de predicción generada.
    
    Args:
        moto_id: ID de la moto
        tipo_prediccion: Tipo de predicción
        confianza: Nivel de confianza (0.0 - 1.0)
        severidad: Severidad (info, low, medium, high)
        details: Detalles de la predicción
        sensor_id: ID del sensor (opcional)
        component_id: ID del componente (opcional)
        suggested_action: Acción sugerida (opcional)
        correlation_id: ID de correlación (opcional)
        metadata: Metadata adicional (opcional)
    """
    event = PrediccionGeneradaEvent(
        timestamp=datetime.now(timezone.utc),
        moto_id=moto_id,
        sensor_id=sensor_id,
        component_id=component_id,
        tipo_prediccion=tipo_prediccion,
        confianza=confianza,
        severidad=severidad,
        details=details,
        suggested_action=suggested_action,
        correlation_id=correlation_id,
        metadata=metadata or {}
    )
    await event.emit()
