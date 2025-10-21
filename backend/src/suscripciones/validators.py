"""
Validadores personalizados para suscripciones.
"""
from datetime import datetime, timedelta
from typing import Optional

from .models import PlanType, SuscripcionStatus


def validate_plan(plan: str) -> tuple[bool, Optional[str]]:
    """
    Valida tipo de plan.
    
    Args:
        plan: Plan a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    valid_plans = [p.value for p in PlanType]
    
    if plan not in valid_plans:
        return False, f"Plan inválido. Debe ser uno de: {', '.join(valid_plans)}"
    
    return True, None


def validate_status(status: str) -> tuple[bool, Optional[str]]:
    """
    Valida estado de suscripción.
    
    Args:
        status: Estado a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    valid_statuses = [s.value for s in SuscripcionStatus]
    
    if status not in valid_statuses:
        return False, f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
    
    return True, None


def validate_date_range(
    start_date: datetime,
    end_date: Optional[datetime]
) -> tuple[bool, Optional[str]]:
    """
    Valida rango de fechas.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if end_date and end_date <= start_date:
        return False, "La fecha de fin debe ser posterior a la fecha de inicio"
    
    return True, None


def validate_precio(precio: Optional[float], plan: str) -> tuple[bool, Optional[str]]:
    """
    Valida precio según el plan.
    
    Args:
        precio: Precio a validar
        plan: Tipo de plan
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if plan == PlanType.FREEMIUM:
        if precio is not None and precio > 0:
            return False, "El plan freemium no debe tener precio"
    
    if plan == PlanType.PREMIUM:
        if precio is None or precio <= 0:
            return False, "El plan premium debe tener un precio mayor a 0"
        
        # Precio razonable (máximo $9999.99)
        if precio > 9999.99:
            return False, "El precio no puede exceder $9,999.99"
    
    return True, None


def validate_metodo_pago(
    metodo_pago: Optional[str],
    plan: str
) -> tuple[bool, Optional[str]]:
    """
    Valida método de pago según el plan.
    
    Args:
        metodo_pago: Método de pago
        plan: Tipo de plan
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    valid_metodos = ["tarjeta", "paypal", "transferencia", "mercadopago", "stripe"]
    
    if plan == PlanType.PREMIUM and not metodo_pago:
        return False, "El plan premium requiere un método de pago"
    
    if metodo_pago and metodo_pago.lower() not in valid_metodos:
        return False, f"Método de pago inválido. Debe ser uno de: {', '.join(valid_metodos)}"
    
    return True, None


def validate_duracion(duracion_meses: int) -> tuple[bool, Optional[str]]:
    """
    Valida duración de suscripción en meses.
    
    Args:
        duracion_meses: Duración en meses
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if duracion_meses < 1:
        return False, "La duración debe ser al menos 1 mes"
    
    if duracion_meses > 24:
        return False, "La duración no puede exceder 24 meses"
    
    return True, None


def calculate_end_date(start_date: datetime, duracion_meses: int) -> datetime:
    """
    Calcula fecha de fin según duración.
    
    Args:
        start_date: Fecha de inicio
        duracion_meses: Duración en meses
        
    Returns:
        Fecha de fin calculada
    """
    # Aproximación: 30 días por mes
    return start_date + timedelta(days=duracion_meses * 30)
