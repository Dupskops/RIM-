"""
Validadores para el módulo de suscripciones v2.3 Freemium.

Proporciona funciones de validación para requests de suscripciones,
alineados con la arquitectura v2.3 (Free/Pro sin sistema de pagos).
"""
from __future__ import annotations

from typing import Optional, Any, Dict, Union

from pydantic import BaseModel

from .schemas import (
    CambiarPlanRequest,
    SuscripcionCancelRequest,
)


# Claves de características válidas en v2.3
CARACTERISTICAS_VALIDAS = {
    "CHATBOT",
    "ML_PREDICTIONS", 
    "EXPORT_REPORTS",
    "CUSTOM_ALERTS",
    "MULTI_BIKE",
    "NOTIFICATIONS",
    "REPORTS",
    "ALERTS",
    "MOTO_REGISTER",
    "SENSOR_VIEW",
    "DASHBOARD",
}


def validate_clave_caracteristica(clave: str) -> tuple[bool, Optional[str]]:
    """Valida que la clave de característica sea válida.
    
    Args:
        clave: Clave de la característica (ej: 'CHATBOT', 'ML_PREDICTIONS')
        
    Returns:
        Tupla (valido, mensaje_error)
    """
    if not clave or not clave.strip():
        return False, "La clave de característica no puede estar vacía"
    
    clave_upper = clave.upper()
    
    if clave_upper not in CARACTERISTICAS_VALIDAS:
        return False, (
            f"Característica '{clave}' no válida. "
            f"Debe ser una de: {', '.join(sorted(CARACTERISTICAS_VALIDAS))}"
        )
    
    return True, None


def validate_cambiar_plan_payload(
    payload: Union[Dict[str, Any], CambiarPlanRequest]
) -> tuple[bool, Optional[str]]:
    """Valida el payload para cambiar de plan.
    
    Args:
        payload: Dict o CambiarPlanRequest con plan_id
        
    Returns:
        Tupla (valido, mensaje_error)
    """
    if isinstance(payload, BaseModel):
        # Si ya es un BaseModel validado por Pydantic, confiar en la validación
        return True, None
    
    # Validación para dict (por compatibilidad)
    data = dict(payload or {})
    
    plan_id = data.get("plan_id")
    
    if not isinstance(plan_id, int):
        return False, "plan_id debe ser un entero"
    
    if plan_id <= 0:
        return False, "plan_id debe ser mayor a 0"
    
    return True, None


def validate_cancel_payload(
    payload: Union[Dict[str, Any], SuscripcionCancelRequest]
) -> tuple[bool, Optional[str]]:
    """Valida el payload para cancelar suscripción.
    
    En v2.3 Freemium solo se usa mode='immediate' (cancelación inmediata).
    
    Args:
        payload: Dict o SuscripcionCancelRequest
        
    Returns:
        Tupla (valido, mensaje_error)
    """
    if isinstance(payload, BaseModel):
        # Si ya es un BaseModel validado por Pydantic, confiar en la validación
        data = payload.model_dump()
    else:
        data = dict(payload or {})
    
    mode = data.get("mode")
    if mode not in {"immediate", "end_of_period"}:
        return False, "mode debe ser 'immediate' o 'end_of_period'"
    
    reason = data.get("reason")
    if reason is not None:
        if not isinstance(reason, str):
            return False, "reason debe ser un string"
        if len(reason) > 1000:
            return False, "reason no puede exceder 1000 caracteres"
    
    return True, None


def validate_usuario_id(usuario_id: Any) -> tuple[bool, Optional[str]]:
    """Valida que usuario_id sea un entero positivo.
    
    Args:
        usuario_id: ID del usuario a validar
        
    Returns:
        Tupla (valido, mensaje_error)
    """
    if not isinstance(usuario_id, int):
        return False, "usuario_id debe ser un entero"
    
    if usuario_id <= 0:
        return False, "usuario_id debe ser mayor a 0"
    
    return True, None


def validate_plan_id(plan_id: Any) -> tuple[bool, Optional[str]]:
    """Valida que plan_id sea un entero positivo.
    
    Args:
        plan_id: ID del plan a validar
        
    Returns:
        Tupla (valido, mensaje_error)
    """
    if not isinstance(plan_id, int):
        return False, "plan_id debe ser un entero"
    
    if plan_id <= 0:
        return False, "plan_id debe ser mayor a 0"
    
    return True, None


__all__ = [
    "CARACTERISTICAS_VALIDAS",
    "validate_clave_caracteristica",
    "validate_cambiar_plan_payload",
    "validate_cancel_payload",
    "validate_usuario_id",
    "validate_plan_id",
]

