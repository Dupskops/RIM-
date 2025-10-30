"""
Servicios de lógica de negocio para suscripciones.

Este servicio expone utilidades que usan los casos de uso en
`use_cases.py`. Está adaptado a los modelos actuales en
`models.py` y a los helpers en `validators.py`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Any, Dict
import math

from .models import Suscripcion, Plan, EstadoSuscripcion
from .validators import calculate_end_date
from .repositories import SuscripcionRepository


class SuscripcionService:
    """Servicio con lógica de negocio para suscripciones.

    Provee helpers pequeños y determinísticos que los casos de uso
    pueden invocar, por ejemplo para preparar datos antes de crear
    una suscripción o para validar reglas simples (cancelación,
    renovación, upgrade).
    """

    @staticmethod
    def prepare_suscripcion_data(
        usuario_id: int,
        plan: Any,
        duracion_meses: Optional[int] = None,
        precio: Optional[Decimal | float | None] = None,
        metodo_pago: Optional[str] = None,
        transaction_id: Optional[str] = None,
        auto_renovacion: bool = False,
        notas: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Prepara un dict con los campos esperados por el repository.

        Normaliza nombres a los usados en el modelo (`usuario_id`,
        `plan_id`, `fecha_inicio`, `fecha_fin`, `estado_suscripcion`, etc.).

        - `plan` puede ser un objeto `Plan`, un dict con `id` o un `plan_id`.
        - `duracion_meses` solo se usa para calcular `fecha_fin` cuando
          aplica.
        """
        ahora = datetime.now(timezone.utc)

        # Determinar plan_id y, si es posible, nombre/objeto plan
        plan_id: Optional[int] = None
        plan_obj: Optional[Plan] = None
        if isinstance(plan, Plan):
            plan_obj = plan
            plan_id = getattr(plan, "id", None)
        elif isinstance(plan, dict):
            plan_id = plan.get("id")
        elif isinstance(plan, int):
            plan_id = plan

        fecha_fin = None
        # Intentamos detectar si el plan es "premium" por nombre si tenemos el objeto
        nombre_plan = getattr(plan_obj, "nombre_plan", "") if plan_obj else ""
        if ("premium" in str(nombre_plan).lower() or (plan_obj is None and duracion_meses)) and duracion_meses:
            fecha_fin = calculate_end_date(ahora, duracion_meses)

        return {
            "usuario_id": usuario_id,
            "plan_id": plan_id,
            "fecha_inicio": ahora,
            "fecha_fin": fecha_fin,
            "estado_suscripcion": EstadoSuscripcion.ACTIVA,
            "precio": Decimal(str(precio)) if precio is not None else None,
            "metodo_pago": metodo_pago.lower() if metodo_pago else None,
            "transaction_id": transaction_id,
            "auto_renovacion": bool(auto_renovacion),
            "notas": notas,
        }

    @staticmethod
    def can_upgrade(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """Determina si se puede hacer upgrade a premium.

        Regla simple: si el plan actual contiene 'premium' en su nombre,
        no se puede upgrade; además la suscripción debe estar activa.
        """
        plan_nombre = None
        if hasattr(suscripcion, "plan") and suscripcion.plan is not None:
            plan_nombre = getattr(suscripcion.plan, "nombre_plan", None)

        if plan_nombre and "premium" in str(plan_nombre).lower():
            return False, "Ya tienes una suscripción premium activa"

        if getattr(suscripcion, "estado_suscripcion", None) != EstadoSuscripcion.ACTIVA:
            return False, "La suscripción no está activa"

        return True, None

    @staticmethod
    def can_cancel(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """Verifica si la suscripción puede cancelarse.

        Regla: no puede cancelarse si ya está en estado CANCELADA.
        """
        if getattr(suscripcion, "estado_suscripcion", None) == EstadoSuscripcion.CANCELADA:
            return False, "La suscripción ya está cancelada"

        return True, None

    @staticmethod
    def can_renew(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """Verifica si una suscripción puede renovarse.

        Regla simple: solo planes 'premium' pueden renovarse y no pueden
        estar cancelados.
        """
        plan_nombre = None
        if hasattr(suscripcion, "plan") and suscripcion.plan is not None:
            plan_nombre = getattr(suscripcion.plan, "nombre_plan", None)

        if not plan_nombre or "premium" not in str(plan_nombre).lower():
            return False, "Solo suscripciones premium pueden renovarse"

        if getattr(suscripcion, "estado_suscripcion", None) == EstadoSuscripcion.CANCELADA:
            return False, "No se puede renovar una suscripción cancelada"

        return True, None

    @staticmethod
    def calculate_pagination(total: int, page: int, page_size: int) -> dict:
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    def build_suscripcion_response(suscripcion: Suscripcion) -> dict:
        """Construye un dict acorde a `SuscripcionUsuarioReadSchema`.

        Devuelve las llaves: `suscripcion_id`, `plan`, `estado_suscripcion`,
        `fecha_inicio`, `fecha_fin`.
        """
        plan_field = None
        if hasattr(suscripcion, "plan") and suscripcion.plan is not None:
            p = suscripcion.plan
            # Intentar mapear los campos más relevantes del plan
            plan_field = {
                "id": getattr(p, "id", None),
                "nombre_plan": getattr(p, "nombre_plan", None),
                "precio": getattr(p, "precio", None),
                "periodo_facturacion": getattr(p, "periodo_facturacion", None),
                "caracteristicas": getattr(p, "caracteristicas", []) or [],
            }
        else:
            # si no hay relación cargada, intentar usar plan_id
            plan_field = {"id": getattr(suscripcion, "plan_id", None)}

        return {
            "suscripcion_id": getattr(suscripcion, "id", None),
            "plan": plan_field,
            "estado_suscripcion": str(getattr(suscripcion, "estado_suscripcion", None)),
            "fecha_inicio": getattr(suscripcion, "fecha_inicio", None),
            "fecha_fin": getattr(suscripcion, "fecha_fin", None),
        }

    async def apply_successful_payment(self, transaccion: object, repository: SuscripcionRepository) -> Optional[Suscripcion]:
        """Aplica los efectos de una transacción exitosa sobre la suscripción.

        - Busca el plan y asigna el plan al usuario usando el repository.
        - Calcula `fecha_fin` según `periodo_facturacion` del plan (mensual=1, anual=12, unico=None).

        Args:
            transaccion: objeto que contiene al menos `usuario_id`, `plan_id`, `monto`.
            repository: instancia de `SuscripcionRepository` con sesión.

        Returns:
            La instancia `Suscripcion` creada/actualizada o None si no se pudo aplicar.
        """
        if repository is None:
            return None

        usuario_id = getattr(transaccion, "usuario_id", None)
        plan_id = getattr(transaccion, "plan_id", None)
        if not usuario_id or not plan_id:
            return None

        # Obtener datos del plan
        plan = await repository.get_plan_by_id(plan_id)
        duracion_meses = None
        if plan is not None:
            periodo = getattr(plan, "periodo_facturacion", None)
            if periodo:
                periodo_str = str(periodo).lower()
                if "mensual" in periodo_str:
                    duracion_meses = 1
                elif "anual" in periodo_str:
                    duracion_meses = 12
                else:
                    duracion_meses = None

        start_date = datetime.now(timezone.utc)
        fecha_fin = calculate_end_date(start_date, duracion_meses) if duracion_meses else None

        # Delegar al repository para asignar el plan
        assigned = await repository.assign_plan_to_user(
            usuario_id=usuario_id,
            plan_id=plan_id,
            fecha_inicio=start_date,
            fecha_fin=fecha_fin,
        )

        return assigned


__all__ = [
    "SuscripcionService",
]
