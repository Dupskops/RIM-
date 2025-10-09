"""
Utilidades compartidas del sistema RIM.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import hashlib
import secrets
import re


# ============================================
# UTILIDADES DE FECHA Y HORA
# ============================================
def now() -> datetime:
    """Retorna la fecha y hora actual."""
    return datetime.now()


def add_days(date: datetime, days: int) -> datetime:
    """Añade días a una fecha."""
    return date + timedelta(days=days)


def is_expired(expiration_date: datetime) -> bool:
    """Verifica si una fecha ha expirado."""
    return datetime.now() > expiration_date


def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Formatea un datetime como string."""
    return dt.strftime(format)


def days_until(target_date: datetime) -> int:
    """Calcula días hasta una fecha objetivo."""
    delta = target_date - datetime.now()
    return max(0, delta.days)


# ============================================
# UTILIDADES DE SEGURIDAD
# ============================================
def generate_token(length: int = 32) -> str:
    """Genera un token aleatorio seguro."""
    return secrets.token_urlsafe(length)


def hash_string(text: str) -> str:
    """Crea hash SHA-256 de un string."""
    return hashlib.sha256(text.encode()).hexdigest()


# ============================================
# VALIDACIONES
# ============================================
def is_valid_email(email: str) -> bool:
    """Valida formato de email."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """Valida formato de teléfono (simple)."""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitiza un string eliminando caracteres peligrosos."""
    # Elimina caracteres de control
    sanitized = ''.join(char for char in text if ord(char) >= 32)
    return sanitized[:max_length].strip()


# ============================================
# UTILIDADES DE DATOS
# ============================================
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """División segura que retorna default si el denominador es 0."""
    return numerator / denominator if denominator != 0 else default


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Limita un valor entre min y max."""
    return max(min_value, min(value, max_value))


def percentage(part: float, total: float) -> float:
    """Calcula porcentaje con manejo de división por 0."""
    return safe_divide(part * 100, total, 0.0)


def round_to_decimals(value: float, decimals: int = 2) -> float:
    """Redondea a n decimales."""
    return round(value, decimals)


# ============================================
# CONVERSIÓN DE DATOS
# ============================================
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convierte Celsius a Fahrenheit."""
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convierte Fahrenheit a Celsius."""
    return (fahrenheit - 32) * 5/9


def km_to_miles(km: float) -> float:
    """Convierte kilómetros a millas."""
    return km * 0.621371


def miles_to_km(miles: float) -> float:
    """Convierte millas a kilómetros."""
    return miles * 1.60934


def bar_to_psi(bar: float) -> float:
    """Convierte bar a PSI."""
    return bar * 14.5038


def psi_to_bar(psi: float) -> float:
    """Convierte PSI a bar."""
    return psi / 14.5038


# ============================================
# UTILIDADES DE FORMATEO
# ============================================
def format_sensor_value(value: float, sensor_type: str, decimals: int = 2) -> str:
    """Formatea un valor de sensor con su unidad."""
    from .constants import SENSOR_RANGES, TipoSensor
    
    rounded_value = round(value, decimals)
    
    # Obtener unidad del rango de sensores
    try:
        sensor_enum = TipoSensor(sensor_type)
        unit = SENSOR_RANGES.get(sensor_enum, {}).get("unit", "")
        return f"{rounded_value} {unit}"
    except (ValueError, KeyError):
        return str(rounded_value)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Trunca texto a una longitud máxima."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# ============================================
# UTILIDADES DE DICCIONARIOS
# ============================================
def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Hace merge profundo de dos diccionarios."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Elimina valores None de un diccionario."""
    return {k: v for k, v in data.items() if v is not None}


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Aplana un diccionario anidado."""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# ============================================
# UTILIDADES DE PAGINACIÓN
# ============================================
def paginate(items: list, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Pagina una lista de items.
    
    Returns:
        {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 10,
            "total_pages": 10
        }
    """
    total = len(items)
    total_pages = (total + page_size - 1) // page_size  # Ceil division
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


# ============================================
# UTILIDADES DE IDs
# ============================================
def generate_id(prefix: str = "") -> str:
    """Genera un ID único con prefijo opcional."""
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def is_valid_uuid(uuid_string: str) -> bool:
    """Valida si un string es un UUID válido."""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False
