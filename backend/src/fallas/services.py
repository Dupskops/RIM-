"""
Servicios de lógica de negocio para fallas.
Funciones auxiliares y operaciones específicas del dominio.
"""
from typing import Optional, List
from datetime import datetime

from .models import Falla
from .validators import (
    validate_tipo_falla,
    validate_severidad,
    validate_confianza_ml,
    is_falla_critica,
    calculate_dias_resolucion
)
from ..shared.constants import TipoFalla, SeveridadFalla, EstadoFalla
from ..shared.utils import safe_divide, percentage


def generate_codigo_falla() -> str:
    """
    Genera un código único para una falla.
    
    Returns:
        Código en formato FL-YYYYMMDD-XXX
    """
    from datetime import datetime
    import random
    
    fecha = datetime.now().strftime("%Y%m%d")
    numero = random.randint(1, 999)
    return f"FL-{fecha}-{numero:03d}"


def determine_severidad_from_sensor(
    valor_actual: float,
    valor_esperado: float,
    sensor_type: str
) -> str:
    """
    Determina la severidad basándose en la desviación del sensor.
    
    Args:
        valor_actual: Valor actual del sensor
        valor_esperado: Valor esperado
        sensor_type: Tipo de sensor
        
    Returns:
        Severidad calculada (baja, media, alta, critica)
    """
    # Calcular desviación porcentual
    desviacion = abs(valor_actual - valor_esperado)
    desviacion_porcentaje = safe_divide(desviacion * 100, abs(valor_esperado), 0.0)
    
    # Determinar severidad según desviación
    if desviacion_porcentaje < 10:
        return SeveridadFalla.BAJA.value
    elif desviacion_porcentaje < 20:
        return SeveridadFalla.MEDIA.value
    elif desviacion_porcentaje < 30:
        return SeveridadFalla.ALTA.value
    else:
        return SeveridadFalla.CRITICA.value


def determine_puede_conducir(tipo_falla: str, severidad: str) -> bool:
    """
    Determina si es seguro conducir con esta falla.
    
    Args:
        tipo_falla: Tipo de falla
        severidad: Severidad de la falla
        
    Returns:
        True si es seguro conducir, False si no
    """
    # Fallas que siempre impiden conducir
    fallas_criticas = [
        TipoFalla.PRESION_ACEITE_BAJA.value,
        TipoFalla.CAIDA_DETECTADA.value,
    ]
    
    if tipo_falla in fallas_criticas:
        return False
    
    # Severidad crítica generalmente no permite conducir
    if severidad == SeveridadFalla.CRITICA.value:
        return False
    
    # Sobrecalentamiento crítico
    if tipo_falla == TipoFalla.SOBRECALENTAMIENTO.value and severidad == SeveridadFalla.ALTA.value:
        return False
    
    return True


def generate_solucion_sugerida(tipo_falla: str, severidad: str) -> str:
    """
    Genera una solución sugerida basándose en el tipo y severidad.
    
    Args:
        tipo_falla: Tipo de falla
        severidad: Severidad
        
    Returns:
        Texto con solución sugerida
    """
    soluciones = {
        TipoFalla.SOBRECALENTAMIENTO.value: (
            "Revisar sistema de refrigeración. "
            "Verificar nivel de líquido refrigerante y funcionamiento del radiador."
        ),
        TipoFalla.BATERIA_BAJA.value: (
            "Revisar sistema de carga. "
            "Verificar batería y alternador. Considerar reemplazo de batería."
        ),
        TipoFalla.PRESION_ACEITE_BAJA.value: (
            "URGENTE: Detener moto inmediatamente. "
            "Verificar nivel de aceite y posibles fugas. Revisar bomba de aceite."
        ),
        TipoFalla.VIBRACIONES_ANORMALES.value: (
            "Revisar balanceo de llantas y suspensiones. "
            "Verificar apriete de componentes y estado de rodamientos."
        ),
        TipoFalla.PRESION_LLANTAS_INCORRECTA.value: (
            "Ajustar presión de llantas según especificaciones del fabricante. "
            "Revisar posibles fugas o daños en las llantas."
        ),
        TipoFalla.SENSOR_DESCONECTADO.value: (
            "Revisar conexión del sensor. "
            "Verificar cableado y reemplazar sensor si está dañado."
        ),
    }
    
    return soluciones.get(tipo_falla, "Contactar con un técnico especializado para diagnóstico completo.")


def calcular_tasa_resolucion(
    total_fallas: int,
    fallas_resueltas: int
) -> float:
    """
    Calcula el porcentaje de fallas resueltas.
    
    Args:
        total_fallas: Total de fallas
        fallas_resueltas: Número de fallas resueltas
        
    Returns:
        Porcentaje de resolución
    """
    return percentage(fallas_resueltas, total_fallas)


def calcular_tiempo_promedio_resolucion(fallas: List[Falla]) -> Optional[float]:
    """
    Calcula el tiempo promedio de resolución en días.
    
    Args:
        fallas: Lista de fallas resueltas
        
    Returns:
        Promedio de días o None si no hay fallas
    """
    fallas_resueltas = [f for f in fallas if f.esta_resuelta and f.fecha_resolucion]
    
    if not fallas_resueltas:
        return None
    
    total_dias = sum(
        calculate_dias_resolucion(f.fecha_deteccion, f.fecha_resolucion)  # type: ignore
        for f in fallas_resueltas
    )
    
    return safe_divide(total_dias, len(fallas_resueltas), 0.0)


def get_prioridad_atencion(falla: Falla) -> int:
    """
    Calcula la prioridad de atención de una falla (1-5, 5 más urgente).
    
    Args:
        falla: Falla a evaluar
        
    Returns:
        Nivel de prioridad (1-5)
    """
    prioridad = 1
    
    # Severidad crítica = máxima prioridad
    if falla.severidad == SeveridadFalla.CRITICA.value:
        prioridad = 5
    elif falla.severidad == SeveridadFalla.ALTA.value:
        prioridad = 4
    elif falla.severidad == SeveridadFalla.MEDIA.value:
        prioridad = 3
    else:
        prioridad = 2
    
    # Si no se puede conducir, aumentar prioridad
    if not falla.puede_conducir:
        prioridad = 5
    
    # Atención inmediata siempre es prioridad máxima
    if falla.requiere_atencion_inmediata:
        prioridad = 5
    
    # Ajustar por tiempo sin resolver
    if falla.dias_sin_resolver > 7 and prioridad < 4:
        prioridad += 1
    
    return min(prioridad, 5)


def should_emit_critical_event(falla: Falla) -> bool:
    """
    Determina si se debe emitir un evento crítico para esta falla.
    
    Args:
        falla: Falla a evaluar
        
    Returns:
        True si debe emitir evento crítico
    """
    return (
        falla.severidad == SeveridadFalla.CRITICA.value or
        falla.requiere_atencion_inmediata or
        not falla.puede_conducir
    )


def estimate_costo_reparacion(tipo_falla: str, severidad: str) -> float:
    """
    Estima el costo de reparación basándose en tipo y severidad.
    
    Args:
        tipo_falla: Tipo de falla
        severidad: Severidad
        
    Returns:
        Costo estimado en moneda local
    """
    # Costos base por tipo de falla
    costos_base = {
        TipoFalla.SOBRECALENTAMIENTO.value: 150.0,
        TipoFalla.BATERIA_BAJA.value: 200.0,
        TipoFalla.PRESION_ACEITE_BAJA.value: 300.0,
        TipoFalla.VIBRACIONES_ANORMALES.value: 100.0,
        TipoFalla.PRESION_LLANTAS_INCORRECTA.value: 50.0,
        TipoFalla.SENSOR_DESCONECTADO.value: 80.0,
    }
    
    costo_base = costos_base.get(tipo_falla, 100.0)
    
    # Multiplicadores por severidad
    multiplicadores = {
        SeveridadFalla.BAJA.value: 1.0,
        SeveridadFalla.MEDIA.value: 1.5,
        SeveridadFalla.ALTA.value: 2.0,
        SeveridadFalla.CRITICA.value: 3.0,
    }
    
    multiplicador = multiplicadores.get(severidad, 1.0)
    
    return costo_base * multiplicador


def get_recomendaciones_preventivas(fallas_historicas: List[Falla]) -> List[str]:
    """
    Genera recomendaciones preventivas basándose en el historial de fallas.
    
    Args:
        fallas_historicas: Lista de fallas pasadas
        
    Returns:
        Lista de recomendaciones
    """
    recomendaciones = []
    
    # Contar tipos de fallas recurrentes
    tipos_conteo = {}
    for falla in fallas_historicas:
        tipos_conteo[falla.tipo] = tipos_conteo.get(falla.tipo, 0) + 1
    
    # Fallas que se repiten mucho
    for tipo, count in tipos_conteo.items():
        if count >= 3:
            recomendaciones.append(
                f"Atención: {count} fallas de tipo '{tipo}'. "
                f"Considerar revisión preventiva de este sistema."
            )
    
    # Fallas críticas recientes
    fallas_criticas = [
        f for f in fallas_historicas[-5:]
        if f.severidad == SeveridadFalla.CRITICA.value
    ]
    
    if len(fallas_criticas) >= 2:
        recomendaciones.append(
            "Se detectaron múltiples fallas críticas recientes. "
            "Recomendamos una revisión completa del vehículo."
        )
    
    return recomendaciones


def can_auto_resolve(falla: Falla) -> bool:
    """
    Determina si una falla puede auto-resolverse.
    
    Args:
        falla: Falla a evaluar
        
    Returns:
        True si puede auto-resolverse
    """
    # Solo fallas de sensores desconectados o falsos positivos
    auto_resolvibles = [
        TipoFalla.SENSOR_DESCONECTADO.value,
        TipoFalla.PRESION_LLANTAS_INCORRECTA.value,  # Si se corrige rápido
    ]
    
    return (
        falla.tipo in auto_resolvibles and
        falla.severidad == SeveridadFalla.BAJA.value and
        falla.origen_deteccion == "sensor"
    )
