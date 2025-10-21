"""
Validadores personalizados para motos.
"""
import re
from typing import Optional


def validate_vin(vin: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de VIN (Vehicle Identification Number).
    
    El VIN debe tener exactamente 17 caracteres alfanuméricos.
    No puede contener las letras I, O, Q (para evitar confusión con 1, 0).
    
    Args:
        vin: VIN a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not vin:
        return False, "El VIN es requerido"
    
    # Remover espacios
    vin = vin.strip().upper()
    
    # Debe tener exactamente 17 caracteres
    if len(vin) != 17:
        return False, "El VIN debe tener exactamente 17 caracteres"
    
    # Solo alfanuméricos
    if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", vin):
        return False, "El VIN solo puede contener letras (excepto I, O, Q) y números"
    
    return True, None


def validate_placa(placa: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de placa.
    
    Formato flexible para diferentes países.
    
    Args:
        placa: Placa a validar
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if not placa:
        return True, None  # Placa es opcional
    
    # Remover espacios
    placa = placa.strip().upper()
    
    # Longitud razonable (3-20 caracteres)
    if len(placa) < 3 or len(placa) > 20:
        return False, "La placa debe tener entre 3 y 20 caracteres"
    
    # Solo alfanuméricos y guiones
    if not re.match(r"^[A-Z0-9\-]+$", placa):
        return False, "La placa solo puede contener letras, números y guiones"
    
    return True, None


def validate_año(año: int) -> tuple[bool, Optional[str]]:
    """
    Valida año de fabricación.
    
    Args:
        año: Año a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Año razonable (desde 1990 hasta año actual + 1)
    from datetime import datetime
    current_year = datetime.now().year
    
    if año < 1990:
        return False, "El año debe ser posterior a 1990"
    
    if año > current_year + 1:
        return False, f"El año no puede ser posterior a {current_year + 1}"
    
    return True, None


def validate_kilometraje(kilometraje: int) -> tuple[bool, Optional[str]]:
    """
    Valida kilometraje.
    
    Args:
        kilometraje: Kilometraje a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if kilometraje < 0:
        return False, "El kilometraje no puede ser negativo"
    
    # Límite razonable (999,999 km)
    if kilometraje > 999999:
        return False, "El kilometraje parece excesivo (máximo 999,999 km)"
    
    return True, None


def validate_marca_ktm(marca: str) -> tuple[bool, Optional[str]]:
    """
    Valida que la marca sea KTM.
    
    Args:
        marca: Marca a validar
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if not marca:
        return False, "La marca es requerida"
    
    if marca.upper() != "KTM":
        return False, "Solo se permiten motos de marca KTM"
    
    return True, None


def validate_modelo(modelo: str) -> tuple[bool, Optional[str]]:
    """
    Valida nombre de modelo.
    
    Args:
        modelo: Modelo a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not modelo or len(modelo.strip()) < 2:
        return False, "El modelo debe tener al menos 2 caracteres"
    
    if len(modelo) > 100:
        return False, "El modelo no puede exceder 100 caracteres"
    
    return True, None
