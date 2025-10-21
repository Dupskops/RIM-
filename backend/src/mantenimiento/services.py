"""
Servicios de lógica de negocio para mantenimiento.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from collections import defaultdict

from src.mantenimiento.models import Mantenimiento
from src.shared.constants import TipoMantenimiento, EstadoMantenimiento
from src.shared.utils import safe_divide, percentage


def generate_codigo_mantenimiento() -> str:
    """
    Genera un código único para el mantenimiento.
    Formato: MN-YYYYMMDD-XXX
    """
    now = datetime.now()
    fecha_str = now.strftime("%Y%m%d")
    ms = now.microsecond // 1000
    return f"MN-{fecha_str}-{ms:03d}"


def calculate_costo_estimado(tipo: TipoMantenimiento) -> float:
    """Calcula el costo estimado según el tipo de mantenimiento."""
    costos_base = {
        TipoMantenimiento.CAMBIO_ACEITE: 50000.0,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 30000.0,
        TipoMantenimiento.CAMBIO_LLANTAS: 400000.0,
        TipoMantenimiento.REVISION_FRENOS: 80000.0,
        TipoMantenimiento.AJUSTE_CADENA: 25000.0,
        TipoMantenimiento.REVISION_GENERAL: 150000.0,
        TipoMantenimiento.CAMBIO_BATERIA: 200000.0,
        TipoMantenimiento.CAMBIO_BUJIAS: 60000.0,
    }
    return costos_base.get(tipo, 100000.0)


def calculate_prioridad_base(tipo: TipoMantenimiento, es_preventivo: bool) -> int:
    """Calcula la prioridad base según tipo y si es preventivo."""
    if not es_preventivo:
        return 4  # Correctivo = alta prioridad
    
    prioridades = {
        TipoMantenimiento.CAMBIO_ACEITE: 4,
        TipoMantenimiento.REVISION_FRENOS: 5,
        TipoMantenimiento.CAMBIO_LLANTAS: 4,
        TipoMantenimiento.CAMBIO_BATERIA: 3,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 3,
        TipoMantenimiento.AJUSTE_CADENA: 3,
        TipoMantenimiento.CAMBIO_BUJIAS: 3,
        TipoMantenimiento.REVISION_GENERAL: 3,
    }
    return prioridades.get(tipo, 3)


def calculate_fecha_vencimiento(
    tipo: TipoMantenimiento,
    fecha_programada: Optional[date] = None
) -> date:
    """Calcula la fecha de vencimiento según el tipo."""
    dias_por_tipo = {
        TipoMantenimiento.CAMBIO_ACEITE: 90,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 180,
        TipoMantenimiento.CAMBIO_LLANTAS: 365,
        TipoMantenimiento.REVISION_FRENOS: 120,
        TipoMantenimiento.AJUSTE_CADENA: 60,
        TipoMantenimiento.REVISION_GENERAL: 180,
        TipoMantenimiento.CAMBIO_BATERIA: 730,  # 2 años
        TipoMantenimiento.CAMBIO_BUJIAS: 365,
    }
    
    dias = dias_por_tipo.get(tipo, 180)
    fecha_base = fecha_programada or date.today()
    return fecha_base + timedelta(days=dias)


def generate_descripcion_automatica(
    tipo: TipoMantenimiento,
    kilometraje: int,
    es_preventivo: bool
) -> str:
    """Genera una descripción automática del mantenimiento."""
    descripciones = {
        TipoMantenimiento.CAMBIO_ACEITE: f"Cambio de aceite y filtro a los {kilometraje:,} km",
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: f"Reemplazo de filtro de aire a los {kilometraje:,} km",
        TipoMantenimiento.CAMBIO_LLANTAS: f"Cambio de llantas delanteras y/o traseras a los {kilometraje:,} km",
        TipoMantenimiento.REVISION_FRENOS: f"Revisión y mantenimiento del sistema de frenos a los {kilometraje:,} km",
        TipoMantenimiento.AJUSTE_CADENA: f"Ajuste y lubricación de cadena de transmisión a los {kilometraje:,} km",
        TipoMantenimiento.REVISION_GENERAL: f"Revisión general completa de la motocicleta a los {kilometraje:,} km",
        TipoMantenimiento.CAMBIO_BATERIA: f"Reemplazo de batería a los {kilometraje:,} km",
        TipoMantenimiento.CAMBIO_BUJIAS: f"Cambio de bujías de encendido a los {kilometraje:,} km",
    }
    
    descripcion = descripciones.get(tipo, f"Mantenimiento de tipo {tipo.value}")
    
    if not es_preventivo:
        descripcion = f"[CORRECTIVO] {descripcion} - Generado por falla detectada"
    
    return descripcion


def determine_urgencia(
    dias_hasta_vencimiento: Optional[int],
    prioridad: int,
    falla_relacionada: bool
) -> bool:
    """Determina si un mantenimiento debe marcarse como urgente."""
    if falla_relacionada:
        return True
    
    if prioridad >= 5:
        return True
    
    if dias_hasta_vencimiento is not None and dias_hasta_vencimiento <= 0:
        return True
    
    if dias_hasta_vencimiento is not None and dias_hasta_vencimiento <= 3 and prioridad >= 4:
        return True
    
    return False


def calculate_tasa_completado(total: int, completados: int) -> float:
    """Calcula la tasa de mantenimientos completados."""
    return percentage(completados, total)


def calculate_duracion_promedio(mantenimientos: List[Mantenimiento]) -> Optional[float]:
    """Calcula la duración promedio en horas."""
    duraciones = []
    for m in mantenimientos:
        if m.duracion_servicio is not None:
            duraciones.append(m.duracion_servicio)
    
    if not duraciones:
        return None
    
    return sum(duraciones) / len(duraciones)


def calculate_costo_promedio(mantenimientos: List[Mantenimiento]) -> float:
    """Calcula el costo promedio."""
    costos = [m.costo_total for m in mantenimientos if m.costo_total is not None]
    if not costos:
        return 0.0
    return sum(costos) / len(costos)


def get_recomendaciones_mantenimiento(
    tipo: TipoMantenimiento,
    kilometraje_actual: int
) -> List[str]:
    """Genera recomendaciones específicas según el tipo de mantenimiento."""
    recomendaciones = {
        TipoMantenimiento.CAMBIO_ACEITE: [
            "Usar aceite sintético de calidad para mejor protección",
            "Revisar nivel de aceite regularmente entre cambios",
            "Cambiar también el filtro de aceite",
            "Verificar que no haya fugas en el motor"
        ],
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: [
            "Limpiar filtro cada 3,000 km si es reutilizable",
            "Usar filtros originales o de alta calidad",
            "Revisar que no entre polvo al motor"
        ],
        TipoMantenimiento.CAMBIO_LLANTAS: [
            "Verificar presión de llantas semanalmente",
            "Rotar llantas según recomendación del fabricante",
            "Revisar desgaste de banda de rodamiento",
            "Balancear llantas después del cambio"
        ],
        TipoMantenimiento.REVISION_FRENOS: [
            "Revisar espesor de pastillas regularmente",
            "Cambiar líquido de frenos cada año",
            "Verificar que no haya fugas en el sistema",
            "Purgar frenos si el pedal se siente esponjoso"
        ],
        TipoMantenimiento.AJUSTE_CADENA: [
            "Lubricar cadena cada 500 km",
            "Limpiar cadena antes de lubricar",
            "Verificar tensión de cadena regularmente",
            "Revisar desgaste de piñones"
        ],
        TipoMantenimiento.REVISION_GENERAL: [
            "Revisar todos los sistemas de la moto",
            "Verificar luces y señales",
            "Revisar suspensión y dirección",
            "Actualizar libro de mantenimiento"
        ],
        TipoMantenimiento.CAMBIO_BATERIA: [
            "Revisar terminales y conexiones",
            "Limpiar bornes antes de instalar",
            "Verificar voltaje regularmente",
            "Mantener cargada si no se usa frecuentemente"
        ],
        TipoMantenimiento.CAMBIO_BUJIAS: [
            "Usar bujías especificadas por el fabricante",
            "Verificar distancia entre electrodos",
            "No sobre-apretar al instalar",
            "Revisar cables de bujías"
        ],
    }
    
    return recomendaciones.get(tipo, ["Seguir recomendaciones del fabricante"])


def predict_next_maintenance_date(
    tipo: TipoMantenimiento,
    kilometraje_actual: int,
    km_promedio_mes: int = 1000
) -> date:
    """Predice la fecha del próximo mantenimiento basado en kilometraje."""
    intervalos_km = {
        TipoMantenimiento.CAMBIO_ACEITE: 5000,
        TipoMantenimiento.CAMBIO_FILTRO_AIRE: 10000,
        TipoMantenimiento.CAMBIO_LLANTAS: 15000,
        TipoMantenimiento.REVISION_FRENOS: 8000,
        TipoMantenimiento.AJUSTE_CADENA: 3000,
        TipoMantenimiento.REVISION_GENERAL: 10000,
        TipoMantenimiento.CAMBIO_BATERIA: 20000,
        TipoMantenimiento.CAMBIO_BUJIAS: 12000,
    }
    
    km_hasta_proximo = intervalos_km.get(tipo, 10000)
    meses_estimados = km_hasta_proximo / km_promedio_mes
    dias_estimados = int(meses_estimados * 30)
    
    return date.today() + timedelta(days=dias_estimados)


def analyze_maintenance_patterns(mantenimientos: List[Mantenimiento]) -> dict:
    """Analiza patrones en el historial de mantenimientos."""
    if not mantenimientos:
        return {
            "frecuencia_promedio_dias": None,
            "tipo_mas_frecuente": None,
            "costo_promedio": 0.0,
            "tasa_preventivo": 0.0,
        }
    
    # Frecuencia promedio
    fechas = [m.fecha_completado or m.created_at for m in mantenimientos if m.fecha_completado or m.created_at]
    if len(fechas) > 1:
        fechas_sorted = sorted(fechas)
        deltas = [(fechas_sorted[i+1] - fechas_sorted[i]).days for i in range(len(fechas_sorted)-1)]
        frecuencia_promedio = sum(deltas) / len(deltas) if deltas else None
    else:
        frecuencia_promedio = None
    
    # Tipo más frecuente
    tipos_count: dict = defaultdict(int)
    for m in mantenimientos:
        tipos_count[m.tipo.value] += 1
    tipo_mas_frecuente = max(tipos_count, key=lambda k: tipos_count[k]) if tipos_count else None  # type: ignore
    
    # Costo promedio
    costo_promedio = calculate_costo_promedio(mantenimientos)
    
    # Tasa de preventivo
    total = len(mantenimientos)
    preventivos = sum(1 for m in mantenimientos if m.es_preventivo)
    tasa_preventivo = percentage(preventivos, total)
    
    return {
        "frecuencia_promedio_dias": frecuencia_promedio,
        "tipo_mas_frecuente": tipo_mas_frecuente,
        "costo_promedio": costo_promedio,
        "tasa_preventivo": tasa_preventivo,
    }


def should_send_alert(mantenimiento: Mantenimiento) -> bool:
    """Determina si se debe enviar una alerta."""
    if mantenimiento.alerta_enviada:
        return False
    
    if mantenimiento.estado in [EstadoMantenimiento.COMPLETADO, EstadoMantenimiento.CANCELADO]:
        return False
    
    if mantenimiento.dias_hasta_vencimiento is not None:
        return mantenimiento.dias_hasta_vencimiento <= mantenimiento.dias_anticipacion_alerta
    
    return False


def calculate_efficiency_score(mantenimiento: Mantenimiento) -> Optional[float]:
    """
    Calcula un score de eficiencia del mantenimiento (0-100).
    Considera: tiempo de completado, variación de costo, cumplimiento de fecha.
    """
    if mantenimiento.estado != EstadoMantenimiento.COMPLETADO:
        return None
    
    score = 100.0
    
    # Penalización por tiempo excesivo (si tarda más de 8 horas)
    if mantenimiento.duracion_servicio and mantenimiento.duracion_servicio > 8:
        penalizacion = min(20, (mantenimiento.duracion_servicio - 8) * 2)
        score -= penalizacion
    
    # Penalización por sobrecosto (más del 20%)
    if mantenimiento.porcentaje_variacion_costo and mantenimiento.porcentaje_variacion_costo > 20:
        penalizacion = min(30, mantenimiento.porcentaje_variacion_costo - 20)
        score -= penalizacion
    
    # Penalización por completado fuera de fecha
    if mantenimiento.fecha_programada and mantenimiento.fecha_completado:
        fecha_completado_date = mantenimiento.fecha_completado.date()
        dias_diferencia = abs((fecha_completado_date - mantenimiento.fecha_programada).days)
        if dias_diferencia > 3:
            penalizacion = min(20, dias_diferencia * 2)
            score -= penalizacion
    
    return max(0.0, score)
