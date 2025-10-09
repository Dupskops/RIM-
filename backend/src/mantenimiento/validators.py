"""
Validadores de reglas de negocio para mantenimiento.
"""
from datetime import datetime, date, timedelta
from typing import Optional

from src.mantenimiento.models import Mantenimiento
from src.shared.constants import TipoMantenimiento, EstadoMantenimiento


def validate_tipo_mantenimiento(tipo: TipoMantenimiento) -> bool:
    """Valida que el tipo de mantenimiento sea válido."""
    return tipo in TipoMantenimiento


def validate_estado_mantenimiento(estado: EstadoMantenimiento) -> bool:
    """Valida que el estado de mantenimiento sea válido."""
    return estado in EstadoMantenimiento


def validate_transition_estado(
    estado_actual: EstadoMantenimiento,
    nuevo_estado: EstadoMantenimiento
) -> bool:
    """
    Valida transiciones de estado válidas.
    
    Flujo: PENDIENTE -> PROGRAMADO -> EN_PROCESO -> COMPLETADO
                                    -> CANCELADO
    """
    transiciones_validas = {
        EstadoMantenimiento.PENDIENTE: [
            EstadoMantenimiento.PROGRAMADO,
            EstadoMantenimiento.EN_PROCESO,
            EstadoMantenimiento.CANCELADO
        ],
        EstadoMantenimiento.PROGRAMADO: [
            EstadoMantenimiento.EN_PROCESO,
            EstadoMantenimiento.CANCELADO,
            EstadoMantenimiento.PENDIENTE
        ],
        EstadoMantenimiento.EN_PROCESO: [
            EstadoMantenimiento.COMPLETADO,
            EstadoMantenimiento.CANCELADO
        ],
        EstadoMantenimiento.COMPLETADO: [],
        EstadoMantenimiento.CANCELADO: [
            EstadoMantenimiento.PENDIENTE,
            EstadoMantenimiento.PROGRAMADO
        ]
    }
    
    return nuevo_estado in transiciones_validas.get(estado_actual, [])


def validate_fechas(
    fecha_programada: Optional[date],
    fecha_vencimiento: Optional[date]
) -> bool:
    """Valida que las fechas sean coherentes."""
    if fecha_programada and fecha_vencimiento:
        return fecha_programada <= fecha_vencimiento
    return True


def validate_fecha_programada(fecha: Optional[date]) -> bool:
    """Valida que la fecha programada no sea en el pasado."""
    if fecha is None:
        return True
    return fecha >= date.today()


def validate_kilometraje(kilometraje_actual: int, kilometraje_siguiente: Optional[int]) -> bool:
    """Valida que el kilometraje siguiente sea mayor al actual."""
    if kilometraje_siguiente is None:
        return True
    return kilometraje_siguiente > kilometraje_actual


def validate_costos(
    costo_estimado: Optional[float],
    costo_real: Optional[float],
    costo_repuestos: Optional[float],
    costo_mano_obra: Optional[float]
) -> bool:
    """Valida que los costos sean positivos."""
    if costo_estimado is not None and costo_estimado < 0:
        return False
    if costo_real is not None and costo_real < 0:
        return False
    if costo_repuestos is not None and costo_repuestos < 0:
        return False
    if costo_mano_obra is not None and costo_mano_obra < 0:
        return False
    return True


def validate_prioridad(prioridad: int) -> bool:
    """Valida que la prioridad esté en rango 1-5."""
    return 1 <= prioridad <= 5


def validate_dias_anticipacion(dias: int) -> bool:
    """Valida que los días de anticipación sean razonables."""
    return 1 <= dias <= 30


def validate_confianza_ia(confianza: Optional[float]) -> bool:
    """Valida que la confianza de IA esté entre 0 y 1."""
    if confianza is None:
        return True
    return 0.0 <= confianza <= 1.0


def can_iniciar_mantenimiento(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento puede iniciarse."""
    estados_validos = [
        EstadoMantenimiento.PENDIENTE,
        EstadoMantenimiento.PROGRAMADO
    ]
    return mantenimiento.estado in estados_validos


def can_completar_mantenimiento(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento puede completarse."""
    return mantenimiento.estado == EstadoMantenimiento.EN_PROCESO


def can_cancelar_mantenimiento(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento puede cancelarse."""
    return mantenimiento.estado != EstadoMantenimiento.COMPLETADO


def can_update_mantenimiento(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento puede actualizarse."""
    return mantenimiento.estado != EstadoMantenimiento.COMPLETADO


def can_delete_mantenimiento(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento puede eliminarse."""
    return mantenimiento.estado in [
        EstadoMantenimiento.PENDIENTE,
        EstadoMantenimiento.CANCELADO
    ]


def is_mantenimiento_vencido(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento está vencido."""
    if not mantenimiento.fecha_vencimiento:
        return False
    return (
        date.today() > mantenimiento.fecha_vencimiento and
        mantenimiento.estado not in [
            EstadoMantenimiento.COMPLETADO,
            EstadoMantenimiento.CANCELADO
        ]
    )


def is_mantenimiento_urgente(mantenimiento: Mantenimiento) -> bool:
    """Verifica si un mantenimiento es urgente."""
    return (
        mantenimiento.es_urgente or
        mantenimiento.prioridad >= 4 or
        is_mantenimiento_vencido(mantenimiento)
    )


def necesita_alerta(mantenimiento: Mantenimiento) -> bool:
    """Verifica si se debe enviar alerta."""
    if mantenimiento.alerta_enviada:
        return False
    
    if not mantenimiento.fecha_vencimiento:
        return False
    
    if mantenimiento.estado in [
        EstadoMantenimiento.COMPLETADO,
        EstadoMantenimiento.CANCELADO
    ]:
        return False
    
    dias_restantes = (mantenimiento.fecha_vencimiento - date.today()).days
    return dias_restantes <= mantenimiento.dias_anticipacion_alerta


def calculate_dias_hasta_vencimiento(fecha_vencimiento: Optional[date]) -> Optional[int]:
    """Calcula días hasta el vencimiento."""
    if not fecha_vencimiento:
        return None
    delta = fecha_vencimiento - date.today()
    return delta.days


def calculate_duracion_servicio(
    fecha_inicio: Optional[datetime],
    fecha_completado: Optional[datetime]
) -> Optional[int]:
    """Calcula la duración del servicio en horas."""
    if not fecha_inicio or not fecha_completado:
        return None
    delta = fecha_completado - fecha_inicio
    return int(delta.total_seconds() / 3600)


def should_recommend_next_maintenance(
    tipo: TipoMantenimiento,
    kilometraje_actual: int,
    ultimo_kilometraje: Optional[int]
) -> bool:
    """Determina si se debe recomendar el próximo mantenimiento."""
    if ultimo_kilometraje is None:
        return True
    
    # Intervalos recomendados por tipo (en km)
    intervalos = {
        TipoMantenimiento.CAMBIO_ACEITE: 5000,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 10000,
        TipoMantenimiento.CAMBIO_LLANTAS: 15000,
        TipoMantenimiento.REVISION_FRENOS: 8000,
        TipoMantenimiento.AJUSTE_CADENA: 3000,
        TipoMantenimiento.REVISION_GENERAL: 10000,
        TipoMantenimiento.CAMBIO_BATERIA: 20000,
        TipoMantenimiento.CAMBIO_BUJIAS: 12000,
    }
    
    intervalo = intervalos.get(tipo, 10000)
    km_desde_ultimo = kilometraje_actual - ultimo_kilometraje
    
    # Recomendar si ha pasado el 80% del intervalo
    return km_desde_ultimo >= (intervalo * 0.8)


def calculate_kilometraje_siguiente(
    tipo: TipoMantenimiento,
    kilometraje_actual: int
) -> int:
    """Calcula el kilometraje sugerido para el próximo mantenimiento."""
    intervalos = {
        TipoMantenimiento.CAMBIO_ACEITE: 5000,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 10000,
        TipoMantenimiento.CAMBIO_LLANTAS: 15000,
        TipoMantenimiento.REVISION_FRENOS: 8000,
        TipoMantenimiento.AJUSTE_CADENA: 3000,
        TipoMantenimiento.REVISION_GENERAL: 10000,
        TipoMantenimiento.CAMBIO_BATERIA: 20000,
        TipoMantenimiento.CAMBIO_BUJIAS: 12000,
    }
    
    intervalo = intervalos.get(tipo, 10000)
    return kilometraje_actual + intervalo


def validate_mantenimiento_completado(
    notas_tecnico: str,
    costo_real: float
) -> bool:
    """Valida que los datos de completado sean válidos."""
    return len(notas_tecnico) >= 10 and costo_real >= 0
