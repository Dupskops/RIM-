"""
Validadores personalizados para usuarios.
Reutiliza validadores de auth y agrega específicos.
"""
from typing import Optional

# Reutilizar validadores de auth
from src.auth.validators import (
    validate_email_format,
    validate_password_strength,
    validate_phone_number,
    validate_nombre,
)

__all__ = [
    "validate_email_format",
    "validate_password_strength",
    "validate_phone_number",
    "validate_nombre",
]
