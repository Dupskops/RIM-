"""
Validadores de negocio para sensores.
"""
from typing import Tuple
from datetime import datetime

from ..shared.constants import TipoSensor, SENSOR_RANGES


def validate_tipo_sensor(tipo: str) -> Tuple[bool, str]:
    """
    Valida que el tipo de sensor sea válido.
    
    Args:
        tipo: Tipo de sensor
        
    Returns:
        (es_valido, mensaje_error)
    """
    try:
        TipoSensor(tipo)
        return True, ""
    except ValueError:
        valid_types = [t.value for t in TipoSensor]
        return False, f"Tipo de sensor inválido. Tipos válidos: {', '.join(valid_types)}"


def validate_codigo_sensor(codigo: str) -> Tuple[bool, str]:
    """
    Valida el código del sensor.
    
    Args:
        codigo: Código del sensor
        
    Returns:
        (es_valido, mensaje_error)
    """
    if not codigo or len(codigo) < 3:
        return False, "El código del sensor debe tener al menos 3 caracteres"
    
    if len(codigo) > 50:
        return False, "El código del sensor no puede exceder 50 caracteres"
    
    # Solo permitir alfanuméricos, guiones y guiones bajos
    if not all(c.isalnum() or c in ['-', '_'] for c in codigo):
        return False, "El código solo puede contener letras, números, guiones y guiones bajos"
    
    return True, ""


def validate_frecuencia_lectura(frecuencia: int) -> Tuple[bool, str]:
    """
    Valida la frecuencia de lectura del sensor.
    
    Args:
        frecuencia: Frecuencia en segundos
        
    Returns:
        (es_valido, mensaje_error)
    """
    if frecuencia < 1:
        return False, "La frecuencia de lectura debe ser al menos 1 segundo"
    
    if frecuencia > 3600:
        return False, "La frecuencia de lectura no puede exceder 1 hora (3600 segundos)"
    
    return True, ""


def validate_umbrales(
    tipo_sensor: str,
    umbral_min: float | None = None,
    umbral_max: float | None = None
) -> Tuple[bool, str]:
    """
    Valida los umbrales del sensor según el tipo.
    
    Args:
        tipo_sensor: Tipo de sensor
        umbral_min: Umbral mínimo
        umbral_max: Umbral máximo
        
    Returns:
        (es_valido, mensaje_error)
    """
    if umbral_min is not None and umbral_max is not None:
        if umbral_min >= umbral_max:
            return False, "El umbral mínimo debe ser menor que el máximo"
    
    # Validar contra rangos conocidos
    try:
        tipo_enum = TipoSensor(tipo_sensor)
        if tipo_enum in SENSOR_RANGES:
            sensor_range = SENSOR_RANGES[tipo_enum]
            range_min = sensor_range["min"]
            range_max = sensor_range["max"]
            
            if umbral_min is not None and umbral_min < range_min:
                return False, f"Umbral mínimo fuera del rango válido ({range_min}-{range_max})"
            
            if umbral_max is not None and umbral_max > range_max:
                return False, f"Umbral máximo fuera del rango válido ({range_min}-{range_max})"
    except ValueError:
        pass  # Tipo no válido, ya se validó antes
    
    return True, ""


def validate_valor_sensor(tipo_sensor: str, valor: float) -> Tuple[bool, str]:
    """
    Valida que el valor del sensor esté en un rango razonable.
    
    Args:
        tipo_sensor: Tipo de sensor
        valor: Valor leído
        
    Returns:
        (es_valido, mensaje_error)
    """
    # Validaciones básicas
    if valor is None:
        return False, "El valor no puede ser nulo"
    
    # Validar contra rangos físicamente posibles (más amplios que los normales)
    if tipo_sensor == TipoSensor.TEMPERATURA_MOTOR.value:
        if valor < -50 or valor > 200:
            return False, "Temperatura del motor fuera del rango físicamente posible (-50°C a 200°C)"
    
    elif tipo_sensor == TipoSensor.TEMPERATURA_ACEITE.value:
        if valor < -50 or valor > 250:
            return False, "Temperatura del aceite fuera del rango físicamente posible (-50°C a 250°C)"
    
    elif tipo_sensor == TipoSensor.PRESION_ACEITE.value:
        if valor < 0 or valor > 10:
            return False, "Presión de aceite fuera del rango físicamente posible (0-10 bar)"
    
    elif tipo_sensor == TipoSensor.VOLTAJE_BATERIA.value:
        if valor < 0 or valor > 20:
            return False, "Voltaje de batería fuera del rango físicamente posible (0-20V)"
    
    elif tipo_sensor in [TipoSensor.PRESION_LLANTA_DELANTERA.value, TipoSensor.PRESION_LLANTA_TRASERA.value]:
        if valor < 0 or valor > 60:
            return False, "Presión de llanta fuera del rango físicamente posible (0-60 PSI)"
    
    elif tipo_sensor == TipoSensor.VIBRACIONES.value:
        if valor < 0 or valor > 10:
            return False, "Vibraciones fuera del rango físicamente posible (0-10g)"
    
    elif tipo_sensor == TipoSensor.RPM.value:
        if valor < 0 or valor > 20000:
            return False, "RPM fuera del rango físicamente posible (0-20000)"
    
    elif tipo_sensor == TipoSensor.VELOCIDAD.value:
        if valor < 0 or valor > 400:
            return False, "Velocidad fuera del rango físicamente posible (0-400 km/h)"
    
    elif tipo_sensor == TipoSensor.NIVEL_COMBUSTIBLE.value:
        if valor < 0 or valor > 100:
            return False, "Nivel de combustible debe estar entre 0% y 100%"
    
    return True, ""


def is_valor_fuera_rango(tipo_sensor: str, valor: float) -> bool:
    """
    Verifica si un valor está fuera del rango normal (no físicamente posible, sino anormal).
    
    Args:
        tipo_sensor: Tipo de sensor
        valor: Valor leído
        
    Returns:
        True si está fuera del rango normal
    """
    try:
        tipo_enum = TipoSensor(tipo_sensor)
        if tipo_enum not in SENSOR_RANGES:
            return False
        
        sensor_range = SENSOR_RANGES[tipo_enum]
        return valor < sensor_range["min"] or valor > sensor_range["max"]
    except ValueError:
        return False


def get_sensor_unit(tipo_sensor: str) -> str:
    """
    Obtiene la unidad de medida para un tipo de sensor.
    
    Args:
        tipo_sensor: Tipo de sensor
        
    Returns:
        Unidad de medida
    """
    try:
        tipo_enum = TipoSensor(tipo_sensor)
        if tipo_enum in SENSOR_RANGES:
            return SENSOR_RANGES[tipo_enum]["unit"]
    except ValueError:
        pass
    return "unidad"


def validate_timestamp_lectura(timestamp: datetime) -> Tuple[bool, str]:
    """
    Valida el timestamp de una lectura.
    
    Args:
        timestamp: Timestamp de la lectura
        
    Returns:
        (es_valido, mensaje_error)
    """
    now = datetime.utcnow()
    
    # No puede ser en el futuro
    if timestamp > now:
        return False, "El timestamp de la lectura no puede ser en el futuro"
    
    # No puede ser muy antiguo (más de 1 año)
    one_year_ago = datetime(now.year - 1, now.month, now.day)
    if timestamp < one_year_ago:
        return False, "El timestamp de la lectura es demasiado antiguo"
    
    return True, ""
