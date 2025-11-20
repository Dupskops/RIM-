"""
Eventos del módulo de fallas.
Define eventos para comunicación desacoplada con otros módulos.
"""
from dataclasses import dataclass, field
from typing import Optional

from ..shared.event_bus import Event


@dataclass
class FallaDetectadaEvent(Event):
    """
    Evento emitido cuando se detecta una nueva falla.
    
    Suscriptores potenciales:
    - notificaciones: Enviar alerta al usuario
    - ml: Alimentar modelos con nuevos datos
    - mantenimiento: Crear orden de servicio si es necesario
    """
    
    falla_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    severidad: str = ""
    titulo: str = ""
    descripcion: str = ""
    requiere_atencion_inmediata: bool = False
    puede_conducir: bool = True
    origen_deteccion: str = "manual"  # sensor, ml, manual, sistema
    usuario_id: Optional[int] = None
    sensor_id: Optional[int] = None


@dataclass
class FallaCriticaEvent(Event):
    """
    Evento emitido cuando se detecta una falla CRÍTICA.
    Requiere atención inmediata.
    
    Suscriptores potenciales:
    - notificaciones: Enviar alerta urgente (SMS, push, email)
    - usuarios: Notificar al dueño inmediatamente
    - mantenimiento: Crear orden urgente
    """
    
    falla_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    titulo: str = ""
    descripcion: str = ""
    puede_conducir: bool = True
    usuario_id: Optional[int] = None


@dataclass
class FallaDiagnosticadaEvent(Event):
    """
    Evento emitido cuando una falla es diagnosticada.
    
    Suscriptores potenciales:
    - notificaciones: Informar al usuario del diagnóstico
    - mantenimiento: Actualizar orden de servicio
    """
    
    falla_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    solucion_sugerida: str = ""
    usuario_id: Optional[int] = None
    costo_estimado: Optional[float] = None


@dataclass
class FallaResueltaEvent(Event):
    """
    Evento emitido cuando una falla es resuelta.
    
    Suscriptores potenciales:
    - notificaciones: Informar al usuario que está resuelto
    - mantenimiento: Cerrar orden de servicio
    - ml: Registrar resolución exitosa para entrenamiento
    """
    
    falla_id: int = 0
    moto_id: int = 0
    tipo: str = ""
    solucion_aplicada: str = ""
    costo_real: float = 0.0
    dias_resolucion: int = 0
    usuario_id: Optional[int] = None


@dataclass
class FallaMLPredictedEvent(Event):
    """
    Evento emitido cuando ML predice una falla potencial.
    
    Suscriptores potenciales:
    - notificaciones: Alertar de mantenimiento preventivo
    - mantenimiento: Sugerir servicio preventivo
    - usuarios: Mostrar advertencia en app
    """
    
    moto_id: int = 0
    tipo_falla_predicha: str = ""
    probabilidad: float = 0.0  # 0.0 a 1.0
    confianza: float = 0.0
    modelo_ml_usado: str = ""
    usuario_id: Optional[int] = None
    componentes_riesgo: list[str] = field(default_factory=list)
    recomendaciones: list[str] = field(default_factory=list)
