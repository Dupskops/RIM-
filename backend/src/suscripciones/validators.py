"""
Validadores para el módulo de suscripciones.

Proporciona funciones de validación (devuelven tupla (bool, Optional[str]))
pensadas para usarse desde los endpoints antes de persistir o procesar
la lógica de negocio. Están alineados con `src/suscripciones/schemas.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional, Any, Dict, Union

from pydantic import BaseModel

from .schemas import (
    CheckoutCreateRequest,
    SuscripcionCancelRequest,
    AdminAssignSubscriptionRequest,
    PaymentNotificationSchema,
    CancelMode,
)


def _to_decimal(value: Any) -> Union[Decimal, None]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def validate_precio(precio: Optional[Union[Decimal, float, str]], plan: str) -> tuple[bool, Optional[str]]:
    """Compatibilidad: valida precio según el tipo de plan.

    Reglas simples:
    - Si el plan parece 'free'/'freemium' no debe tener precio > 0
    - Si el plan parece 'premium' debe tener precio > 0 y <= 9999.99
    """
    if precio is None:
        # precio ausente es aceptable para freemium o si se usa valor por defecto del plan
        return True, None

    dec = _to_decimal(precio)
    if dec is None:
        return False, "Precio inválido"

    plan_norm = str(plan).lower()
    if "free" in plan_norm or "freemium" in plan_norm:
        if dec is not None and dec > 0:
            return False, "El plan freemium no debe tener precio"

    if "premium" in plan_norm:
        if dec is None or dec <= 0:
            return False, "El plan premium debe tener un precio mayor a 0"
        if dec > Decimal("9999.99"):
            return False, "El precio no puede exceder $9,999.99"

    return True, None


def validate_metodo_pago(metodo_pago: Optional[str], plan: str) -> tuple[bool, Optional[str]]:
    """Compatibilidad: valida método de pago según el plan.

    - Si el plan es premium, se requiere un método de pago
    - Si se provee, debe estar en la lista soportada
    """
    valid_metodos = {"tarjeta", "paypal", "transferencia", "mercadopago", "stripe"}
    plan_norm = str(plan).lower()

    if "premium" in plan_norm and not metodo_pago:
        return False, "El plan premium requiere un método de pago"

    if metodo_pago and metodo_pago.lower() not in valid_metodos:
        return False, f"Método de pago inválido. Debe ser uno de: {', '.join(sorted(valid_metodos))}"

    return True, None


def validate_checkout_payload(payload: Union[Dict[str, Any], CheckoutCreateRequest]) -> tuple[bool, Optional[str]]:
    """Valida el payload de `POST /suscripciones/checkout`.

    Reglas principales:
    - `usuario_id` y `plan_id` deben ser enteros > 0
    - `monto` si existe debe ser Decimal >= 0
    - `payment_method` si existe debe ser string no vacío
    - `metadata` si existe debe ser un dict
    """
    if isinstance(payload, BaseModel):
        data = payload.model_dump()
    else:
        data = dict(payload or {})

    usuario_id = data.get("usuario_id")
    plan_id = data.get("plan_id")

    if not isinstance(usuario_id, int) or usuario_id <= 0:
        return False, "usuario_id inválido"
    if not isinstance(plan_id, int) or plan_id <= 0:
        return False, "plan_id inválido"

    monto_raw = data.get("monto")
    if monto_raw is not None:
        monto = _to_decimal(monto_raw)
        if monto is None:
            return False, "monto inválido"
        if monto < 0:
            return False, "monto debe ser >= 0"

    pm = data.get("payment_method")
    if pm is not None and (not isinstance(pm, str) or not pm.strip()):
        return False, "payment_method inválido"

    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return False, "metadata debe ser un objeto JSON"

    return True, None


def validate_cancel_payload(payload: Union[Dict[str, Any], SuscripcionCancelRequest]) -> tuple[bool, Optional[str]]:
    """Valida `PATCH /suscripciones/{id}/cancel`.

    - `mode` debe ser 'immediate' o 'end_of_period' (validado por enum CancelMode)
    - `reason` si existe no debe ser excesivamente larga
    """
    if isinstance(payload, BaseModel):
        # Si ya es un BaseModel validado por Pydantic, confiar en la validación del enum
        return True, None
    
    # Validación para dict (por compatibilidad)
    data = dict(payload or {})

    mode = data.get("mode")
    if mode not in {"immediate", "end_of_period"}:
        return False, "mode inválido (usar 'immediate' o 'end_of_period')"

    reason = data.get("reason")
    if reason is not None:
        if not isinstance(reason, str) or len(reason) > 1000:
            return False, "reason inválido o demasiado largo (máximo 1000 caracteres)"

    return True, None


def validate_admin_assign_payload(payload: Union[Dict[str, Any], AdminAssignSubscriptionRequest]) -> tuple[bool, Optional[str]]:
    """Valida el body para `POST /admin/suscripciones/assign`.

    - usuario_id y plan_id deben ser enteros > 0
    - si ambas fechas están presentes, fecha_inicio <= fecha_fin
    """
    if isinstance(payload, BaseModel):
        data = payload.model_dump()
    else:
        data = dict(payload or {})

    usuario_id = data.get("usuario_id")
    plan_id = data.get("plan_id")
    if not isinstance(usuario_id, int) or usuario_id <= 0:
        return False, "usuario_id inválido"
    if not isinstance(plan_id, int) or plan_id <= 0:
        return False, "plan_id inválido"

    fecha_inicio = data.get("fecha_inicio")
    fecha_fin = data.get("fecha_fin")
    if fecha_inicio is not None and not isinstance(fecha_inicio, datetime):
        return False, "fecha_inicio inválida"
    if fecha_fin is not None and not isinstance(fecha_fin, datetime):
        return False, "fecha_fin inválida"
    if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
        return False, "fecha_fin debe ser posterior a fecha_inicio"

    return True, None


def validate_payment_notification(payload: Union[Dict[str, Any], PaymentNotificationSchema]) -> tuple[bool, Optional[str]]:
    """Valida el body del webhook `POST /webhooks/payments`.

    - transaccion_id: int > 0
    - payment_token: str no vacío
    - metadata: dict opcional
    """
    if isinstance(payload, BaseModel):
        data = payload.model_dump()
    else:
        data = dict(payload or {})

    tid = data.get("transaccion_id")
    if not isinstance(tid, int) or tid <= 0:
        return False, "transaccion_id inválido"

    token = data.get("payment_token")
    if not isinstance(token, str) or not token.strip():
        return False, "payment_token inválido"
    if len(token) > 128:
        return False, "payment_token demasiado largo"

    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return False, "metadata debe ser un objeto JSON"

    return True, None


def calculate_end_date(start_date: datetime, duracion_meses: int) -> datetime:
    """Calcula fecha de fin (aprox. 30 días por mes)."""
    return start_date + timedelta(days=duracion_meses * 30)


__all__ = [
    "validate_checkout_payload",
    "validate_cancel_payload",
    "validate_admin_assign_payload",
    "validate_payment_notification",
    "_to_decimal",
    "calculate_end_date",
]
