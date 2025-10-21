"""
Eventos del dominio de sensores.
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from src.shared.event_bus import Event


# ==================== EVENT CLASSES ====================

@dataclass
class SensorRegisteredEvent(Event):
    """Evento: Sensor registrado."""
    
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    tipo: str = field(default="")
    codigo: str = field(default="")


@dataclass
class SensorUpdatedEvent(Event):
    """Evento: Sensor actualizado."""
    
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    updated_fields: list[str] = field(default_factory=list)


@dataclass
class SensorDeletedEvent(Event):
    """Evento: Sensor eliminado."""
    
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    codigo: str = field(default="")


@dataclass
class LecturaRegistradaEvent(Event):
    """Evento: Lectura de sensor registrada."""
    
    lectura_id: int = field(default=0)
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    tipo_sensor: str = field(default="")
    valor: float = field(default=0.0)
    unidad: str = field(default="")
    fuera_rango: bool = field(default=False)


@dataclass
class AlertaSensorEvent(Event):
    """Evento: Alerta de sensor generada."""
    
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    tipo_sensor: str = field(default="")
    valor: float = field(default=0.0)
    umbral_violado: str = field(default="")  # "min" o "max"
    severidad: str = field(default="warning")  # warning, critical


@dataclass
class SensorErrorEvent(Event):
    """Evento: Error en sensor detectado."""
    
    sensor_id: int = field(default=0)
    moto_id: int = field(default=0)
    codigo: str = field(default="")
    error_type: str = field(default="")
    error_message: str = field(default="")


# ==================== EMIT HELPER FUNCTIONS ====================

async def emit_sensor_registered(
    sensor_id: int,
    moto_id: int,
    tipo: str,
    codigo: str
) -> None:
    """
    Emite evento de sensor registrado.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        tipo: Tipo de sensor
        codigo: Código del sensor
    """
    event = SensorRegisteredEvent(
        timestamp=datetime.utcnow(),
        sensor_id=sensor_id,
        moto_id=moto_id,
        tipo=tipo,
        codigo=codigo
    )
    await event.emit()


async def emit_sensor_updated(
    sensor_id: int,
    moto_id: int,
    updated_fields: list[str]
) -> None:
    """
    Emite evento de sensor actualizado.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        updated_fields: Campos actualizados
    """
    event = SensorUpdatedEvent(
        timestamp=datetime.utcnow(),
        sensor_id=sensor_id,
        moto_id=moto_id,
        updated_fields=updated_fields
    )
    await event.emit()


async def emit_sensor_deleted(
    sensor_id: int,
    moto_id: int,
    codigo: str
) -> None:
    """
    Emite evento de sensor eliminado.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        codigo: Código del sensor
    """
    event = SensorDeletedEvent(
        timestamp=datetime.utcnow(),
        sensor_id=sensor_id,
        moto_id=moto_id,
        codigo=codigo
    )
    await event.emit()


async def emit_lectura_registrada(
    lectura_id: int,
    sensor_id: int,
    moto_id: int,
    tipo_sensor: str,
    valor: float,
    unidad: str,
    fuera_rango: bool = False
) -> None:
    """
    Emite evento de lectura registrada.
    
    Args:
        lectura_id: ID de la lectura
        sensor_id: ID del sensor
        moto_id: ID de la moto
        tipo_sensor: Tipo de sensor
        valor: Valor leído
        unidad: Unidad de medida
        fuera_rango: Si está fuera de rango
    """
    event = LecturaRegistradaEvent(
        timestamp=datetime.utcnow(),
        lectura_id=lectura_id,
        sensor_id=sensor_id,
        moto_id=moto_id,
        tipo_sensor=tipo_sensor,
        valor=valor,
        unidad=unidad,
        fuera_rango=fuera_rango
    )
    await event.emit()


async def emit_alerta_sensor(
    sensor_id: int,
    moto_id: int,
    tipo_sensor: str,
    valor: float,
    umbral_violado: str,
    severidad: str = "warning"
) -> None:
    """
    Emite evento de alerta de sensor.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        tipo_sensor: Tipo de sensor
        valor: Valor que generó la alerta
        umbral_violado: Umbral violado (min/max)
        severidad: Severidad de la alerta
    """
    event = AlertaSensorEvent(
        timestamp=datetime.utcnow(),
        sensor_id=sensor_id,
        moto_id=moto_id,
        tipo_sensor=tipo_sensor,
        valor=valor,
        umbral_violado=umbral_violado,
        severidad=severidad
    )
    await event.emit()


async def emit_sensor_error(
    sensor_id: int,
    moto_id: int,
    codigo: str,
    error_type: str,
    error_message: str
) -> None:
    """
    Emite evento de error en sensor.
    
    Args:
        sensor_id: ID del sensor
        moto_id: ID de la moto
        codigo: Código del sensor
        error_type: Tipo de error
        error_message: Mensaje de error
    """
    event = SensorErrorEvent(
        timestamp=datetime.utcnow(),
        sensor_id=sensor_id,
        moto_id=moto_id,
        codigo=codigo,
        error_type=error_type,
        error_message=error_message
    )
    await event.emit()
