"""
Eventos del módulo de mantenimiento.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from src.shared.event_bus import Event
from src.shared.constants import TipoMantenimiento, EstadoMantenimiento


@dataclass
class MantenimientoProgramadoEvent(Event):
    """Evento emitido cuando se programa un mantenimiento."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    fecha_programada: Optional[str] = None
    es_preventivo: bool = True
    prioridad: int = 3
    descripcion: str = ""


@dataclass
class MantenimientoUrgenteEvent(Event):
    """Evento emitido cuando se marca un mantenimiento como urgente."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    motivo_urgencia: str = ""
    prioridad: int = 5
    requiere_atencion_inmediata: bool = True


@dataclass
class MantenimientoVencidoEvent(Event):
    """Evento emitido cuando un mantenimiento está vencido."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    fecha_vencimiento: str = ""
    dias_vencido: int = 0
    descripcion: str = ""


@dataclass
class MantenimientoIniciadoEvent(Event):
    """Evento emitido cuando se inicia un mantenimiento."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    mecanico_asignado: str = ""
    taller: str = ""
    fecha_inicio: str = ""


@dataclass
class MantenimientoCompletadoEvent(Event):
    """Evento emitido cuando se completa un mantenimiento."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    duracion_horas: int = 0
    costo_total: float = 0.0
    kilometraje_siguiente: Optional[int] = None
    fecha_completado: str = ""
    repuestos_usados: str = ""


@dataclass
class MantenimientoRecomendadoIAEvent(Event):
    """Evento emitido cuando la IA recomienda un mantenimiento."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    confianza: float = 0.0
    modelo_usado: str = ""
    razon_recomendacion: str = ""
    prioridad_sugerida: int = 3
    fecha_sugerida: Optional[str] = None


@dataclass
class AlertaMantenimientoProximoEvent(Event):
    """Evento emitido cuando se debe alertar sobre un mantenimiento próximo."""
    mantenimiento_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    dias_restantes: int = 0
    fecha_programada: str = ""
    descripcion: str = ""
    es_urgente: bool = False
