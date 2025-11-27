"""
Validadores de negocio para el módulo de motos.

IMPORTANTE: Las validaciones de formato básico (VIN, placa, etc.) están en schemas.py
con Pydantic validators. Este archivo contiene solo validaciones de lógica de negocio
compleja que no pueden expresarse fácilmente en Pydantic.

Versión: v2.3 MVP
"""
from decimal import Decimal


# ============================================
# CONSTANTES DE VALIDACIÓN
# ============================================

KILOMETRAJE_MAX = Decimal("999999.9")

# ============================================
# VALIDADORES DE LÓGICA DE NEGOCIO
# ============================================

def validate_kilometraje(kilometraje: Decimal) -> Decimal:
    """
    Valida que el kilometraje esté en rango permitido.
    
    Reglas:
    - No negativo
    - Máximo 999,999.9 km
    
    Args:
        kilometraje: Valor a validar
        
    Returns:
        Decimal: Kilometraje validado
        
    Raises:
        ValueError: Si el kilometraje está fuera de rango
    """
    if kilometraje < 0:
        raise ValueError("El kilometraje no puede ser negativo")
    if kilometraje > KILOMETRAJE_MAX:
        raise ValueError(f"El kilometraje excede el límite permitido ({KILOMETRAJE_MAX} km)")
    return kilometraje


def validate_kilometraje_no_disminuye(
    kilometraje_nuevo: Decimal,
    kilometraje_actual: Decimal
) -> None:
    """
    Valida regla de negocio: el kilometraje nunca puede disminuir.
    
    Esta es una validación de lógica de negocio que requiere comparar
    con el estado actual de la moto en base de datos.
    
    Args:
        kilometraje_nuevo: Nuevo kilometraje a establecer
        kilometraje_actual: Kilometraje actual en base de datos
        
    Raises:
        ValueError: Si el nuevo kilometraje es menor al actual
    """
    if kilometraje_nuevo < kilometraje_actual:
        raise ValueError(
            f"El kilometraje no puede disminuir "
            f"(actual: {kilometraje_actual} km, nuevo: {kilometraje_nuevo} km)"
        )

