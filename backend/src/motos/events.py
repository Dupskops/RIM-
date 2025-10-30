from dataclasses import dataclass
from datetime import datetime
from src.shared.event_bus import Event
from .models import EstadoSalud


@dataclass
class EstadoCambiadoEvent(Event):
    timestamp: datetime
    moto_id: int
    componente_id: int
    estado_anterior: str
    estado_nuevo: str


@dataclass
class EstadoCriticoDetectadoEvent(Event):
    timestamp: datetime
    moto_id: int
    componente_id: int
    valor_actual: float


@dataclass
class ServicioVencidoEvent(Event):
    timestamp: datetime
    moto_id: int
    kilometraje_actual: float
    tipo_servicio: str


async def emit_estado_cambiado(
    moto_id: int,
    componente_id: int,
    estado_anterior: EstadoSalud,
    estado_nuevo: EstadoSalud
) -> None:
    event = EstadoCambiadoEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        componente_id=componente_id,
        estado_anterior=estado_anterior.value,
        estado_nuevo=estado_nuevo.value
    )
    await event.emit()


async def emit_estado_critico_detectado(
    moto_id: int,
    componente_id: int,
    valor_actual: float
) -> None:
    event = EstadoCriticoDetectadoEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        componente_id=componente_id,
        valor_actual=valor_actual
    )
    await event.emit()


async def emit_servicio_vencido(
    moto_id: int,
    kilometraje_actual: float,
    tipo_servicio: str = "mantenimiento_programado"
) -> None:
    event = ServicioVencidoEvent(
        timestamp=datetime.utcnow(),
        moto_id=moto_id,
        kilometraje_actual=kilometraje_actual,
        tipo_servicio=tipo_servicio
    )
    await event.emit()
