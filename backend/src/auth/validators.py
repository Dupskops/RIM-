"""
Validadores personalizados para autenticación.
"""
import re
from typing import Optional


def validate_email_format(email: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Expresión regular básica para email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, None


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida fortaleza de contraseña.
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número"
    
    # Opcional: Caracteres especiales
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, None


def validate_phone_number(phone: str) -> tuple[bool, Optional[str]]:
    """
    Valida formato de teléfono.
    
    Args:
        phone: Teléfono a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Remover espacios y guiones
    clean_phone = phone.replace(" ", "").replace("-", "")
    
    # Validar formato: +[código país][número] (8-15 dígitos)
    if not re.match(r"^\+?\d{8,15}$", clean_phone):
        return False, "Formato de teléfono inválido. Debe contener entre 8 y 15 dígitos"
    
    return True, None


def validate_nombre(nombre: str) -> tuple[bool, Optional[str]]:
    """
    Valida nombre de usuario.
    
    Args:
        nombre: Nombre a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if len(nombre) < 2:
        return False, "El nombre debe tener al menos 2 caracteres"
    
    if len(nombre) > 255:
        return False, "El nombre no puede exceder 255 caracteres"
    
    # Opcional: Solo letras y espacios
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", nombre):
        return False, "El nombre solo puede contener letras y espacios"
    
    return True, None
