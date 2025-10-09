"""
Eventos del módulo de ML (Machine Learning).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.shared.event_bus import Event


@dataclass
class PrediccionGeneradaEvent(Event):
    """Evento emitido cuando se genera una nueva predicción."""
    prediccion_id: int = 0
    moto_id: int = 0
    usuario_id: int = 0
    tipo: str = ""
    confianza: float = 0.0
    descripcion: str = ""
    es_critica: bool = False
    datos: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrediccionConfirmadaEvent(Event):
    """Evento emitido cuando se confirma una predicción."""
    prediccion_id: int = 0
    moto_id: int = 0
    usuario_id: int = 0
    tipo: str = ""
    confirmada_por: int = 0


@dataclass
class PrediccionFalsaEvent(Event):
    """Evento emitido cuando se marca una predicción como falsa."""
    prediccion_id: int = 0
    moto_id: int = 0
    usuario_id: int = 0
    tipo: str = ""
    marcada_por: int = 0


@dataclass
class ModeloActualizadoEvent(Event):
    """Evento emitido cuando se actualiza un modelo ML."""
    modelo_nombre: str = ""
    version_anterior: str = ""
    version_nueva: str = ""
    metricas: Dict[str, float] = field(default_factory=dict)


@dataclass
class EntrenamientoFinalizadoEvent(Event):
    """Evento emitido cuando finaliza un entrenamiento."""
    entrenamiento_id: int = 0
    modelo_nombre: str = ""
    version: str = ""
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    duracion_segundos: float = 0.0


@dataclass
class AnomaliaDetectadaEvent(Event):
    """Evento emitido cuando se detecta una anomalía."""
    prediccion_id: int = 0
    moto_id: int = 0
    usuario_id: int = 0
    tipo_anomalia: str = ""
    severidad: str = ""
    confianza: float = 0.0
    datos_sensor: Dict[str, Any] = field(default_factory=dict)
