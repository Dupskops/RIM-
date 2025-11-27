"""
Eventos del módulo de motos.

Define eventos de dominio que se emiten cuando ocurren cambios importantes
en el estado de las motos y sus componentes.

Versión: v2.3 MVP
"""
from dataclasses import dataclass
from src.shared.event_bus import Event
from .models import EstadoSalud


# ============================================
# EVENTOS DE ESTADO
# ============================================

@dataclass
class EstadoCambiadoEvent(Event):
    """
    Evento emitido cuando el estado de un componente cambia.
    
    Ejemplo: Motor pasa de BUENO → ATENCION
    
    Suscriptores:
    - Módulo de notificaciones (enviar alerta al usuario)
    - Módulo de fallas (crear falla si estado es CRITICO)
    - Módulo de ML (registrar cambio para entrenamiento)
    """
    moto_id: int = 0  # PK actualizado: usa motos.id
    componente_id: int = 0  # PK actualizado: usa componentes.id
    estado_anterior: str = ""  # EstadoSalud.value
    estado_nuevo: str = ""     # EstadoSalud.value


@dataclass
class EstadoCriticoDetectadoEvent(Event):
    """
    Evento emitido cuando un componente alcanza estado CRITICO.
    
    Este es un evento de alta prioridad que requiere acción inmediata.
    
    Suscriptores:
    - Módulo de notificaciones (enviar push notification urgente)
    - Módulo de fallas (crear falla automática con severidad 'critica')
    - Sistema de alertas (activar alerta sonora/visual en gemelo digital)
    """
    moto_id: int = 0
    componente_id: int = 0
    valor_actual: float = 0.0  # Valor que causó el estado crítico


# ============================================
# EVENTOS DE MANTENIMIENTO
# ============================================

@dataclass
class ServicioVencidoEvent(Event):
    """
    Evento emitido cuando el kilometraje cruza un umbral de servicio.
    
    Intervalos: cada 5000 km (configurable)
    
    Suscriptores:
    - Módulo de mantenimiento (crear mantenimiento preventivo pendiente)
    - Módulo de notificaciones (notificar al usuario)
    - Dashboard (mostrar badge de servicio vencido)
    """
    moto_id: int = 0
    kilometraje_actual: float = 0.0
    tipo_servicio: str = "mantenimiento_programado"


@dataclass
class KilometrajeActualizadoEvent(Event):
    """
    Evento emitido cuando se actualiza el kilometraje de la moto.
    
    Nota: Renombrado de KilometrajeUpdatedEvent para consistencia con español.
    Se mantiene alias por compatibilidad con código antiguo.
    
    Suscriptores:
    - Módulo de mantenimiento (verificar si se vence algún servicio)
    - Módulo de ML (actualizar features de predicción)
    - Dashboard (actualizar indicador de kilometraje)
    """
    moto_id: int = 0
    kilometraje_anterior: float = 0.0
    kilometraje_nuevo: float = 0.0


# Alias por compatibilidad con código antiguo
KilometrajeUpdatedEvent = KilometrajeActualizadoEvent


# ============================================
# FUNCIONES DE EMISIÓN DE EVENTOS
# ============================================

async def emit_estado_cambiado(
    moto_id: int,
    componente_id: int,
    estado_anterior: EstadoSalud,
    estado_nuevo: EstadoSalud
) -> None:
    """
    Emite evento cuando el estado de un componente cambia.
    
    Args:
        moto_id: ID de la moto (motos.id)
        componente_id: ID del componente (componentes.id)
        estado_anterior: Estado previo del componente
        estado_nuevo: Nuevo estado del componente
    """
    event = EstadoCambiadoEvent(
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
    """
    Emite evento de alta prioridad cuando un componente está en estado CRITICO.
    
    Args:
        moto_id: ID de la moto
        componente_id: ID del componente en estado crítico
        valor_actual: Valor de la lectura que causó el estado crítico
    """
    event = EstadoCriticoDetectadoEvent(
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
    """
    Emite evento cuando el kilometraje cruza un umbral de servicio.
    
    Args:
        moto_id: ID de la moto
        kilometraje_actual: Kilometraje actual de la moto
        tipo_servicio: Tipo de servicio requerido (default: mantenimiento_programado)
    """
    event = ServicioVencidoEvent(
        moto_id=moto_id,
        kilometraje_actual=kilometraje_actual,
        tipo_servicio=tipo_servicio
    )
    await event.emit()


async def emit_kilometraje_actualizado(
    moto_id: int,
    kilometraje_anterior: float,
    kilometraje_nuevo: float
) -> None:
    """
    Emite evento cuando se actualiza el kilometraje de la moto.
    
    Args:
        moto_id: ID de la moto
        kilometraje_anterior: Kilometraje antes de la actualización
        kilometraje_nuevo: Nuevo kilometraje actualizado
    """
    event = KilometrajeActualizadoEvent(
        moto_id=moto_id,
        kilometraje_anterior=kilometraje_anterior,
        kilometraje_nuevo=kilometraje_nuevo
    )
    await event.emit()
