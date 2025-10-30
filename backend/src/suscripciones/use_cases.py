"""
Casos de uso del dominio de suscripciones.

Implementa los flujos principales descritos en `docs/USE_CASES.md`:
- Listar planes
- Checkout (crear transacción pending)
- Webhook de pagos (procesar payment_token)
- Cancelar suscripción
- Asignar plan desde admin
- Listar transacciones (historial)

Las implementaciones asumen ciertos métodos en el repository/service; añado
comentarios donde haya que adaptar nombres si difieren en tu proyecto.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from fastapi import HTTPException, status

from .validators import (
    calculate_end_date,
    validate_precio,
    validate_metodo_pago,
    validate_checkout_payload,
    validate_cancel_payload,
    validate_admin_assign_payload,
    validate_payment_notification,
)
from .schemas import (
    CheckoutCreateRequest,
    TransaccionCreateResponse,
    TransaccionReadSchema,
    PaymentNotificationSchema,
    PlanReadSchema,
    SuscripcionUsuarioReadSchema,
    SuscripcionCancelRequest,
    AdminAssignSubscriptionRequest,
)
from .repositories import (
    SuscripcionRepository, 
    PlanesRepository
)

# Usar la paginación centralizada
from ..shared.base_models import create_paginated_response

# Eventos (se espera que exista `src/suscripciones/events.py` con estos helpers)
try:
    from .events import (
        emit_transaccion_creada,
        emit_transaccion_actualizada,
        emit_suscripcion_actualizada,
    )
except Exception:
    # Si no existe el módulo de eventos, definimos stubs que no hacen nada.
    def emit_transaccion_creada(*_args, **_kwargs):
        return None

    def emit_transaccion_actualizada(*_args, **_kwargs):
        return None

    def emit_suscripcion_actualizada(*_args, **_kwargs):
        return None

logger = logging.getLogger(__name__)

class ListPlanesUseCase:
    """Lista los planes disponibles (`GET /planes`)."""

    async def execute(
        self, 
        session: AsyncSession
    ) -> list[PlanReadSchema]:
        planes_repo = PlanesRepository(session)
        # Asume repository.list_planes() que retorna objetos/dicts con los campos del plan
        planes = await planes_repo.list_planes()
        # Normalizar a schema
        result = []
        for p in planes:
            # soporta dicts o atributos
            nombre = p.get("nombre_plan") if isinstance(p, dict) else getattr(p, "nombre_plan", None)
            precio = p.get("precio") if isinstance(p, dict) else getattr(p, "precio", None)
            periodo = p.get("periodo_facturacion") if isinstance(p, dict) else getattr(p, "periodo_facturacion", None)
            caracteristicas = p.get("caracteristicas", []) if isinstance(p, dict) else getattr(p, "caracteristicas", [])
            result.append(PlanReadSchema(id=p.get("id") if isinstance(p, dict) else getattr(p, "id", None), nombre_plan=nombre, precio=Decimal(str(precio)) if precio is not None else Decimal("0.00"), periodo_facturacion=periodo or "", caracteristicas=caracteristicas))
        return result


class CheckoutCreateUseCase:
    """Caso de uso: iniciar checkout (crear Transaccion pending y devolver payment_token).

    Notas/Asunciones:
    - Se asume que `SuscripcionRepository` implementa métodos:
        - `get_plan_by_id(plan_id) -> dict|object` (con `precio` Decimal)
        - `create_transaccion(data) -> transaccion_obj` (crea la transacción y devuelve el objeto con `id`)
      Si los nombres difieren, adapta las llamadas al repositorio.
    - La transacción se crea en estado `pending` y el endpoint devuelve un `payment_token`
      que el cliente usará para simular/confirmar el pago (MVP: '0' = success, '1' = failed).
    - No se marca la transacción como `success`/`failed` aquí; eso lo hará el webhook.
    """

    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service

    async def execute(self, request: CheckoutCreateRequest) -> TransaccionCreateResponse:
        # Validar payload básico
        is_valid, error_msg = validate_checkout_payload(request)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        # Obtener precio del plan si no viene en el request
        plan = await self.repository.get_plan_by_id(request.plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")

        monto = request.monto
        if monto is None:
            # Se espera que `plan.precio` sea Decimal
            monto = getattr(plan, "precio", None)
            if monto is None:
                # Fallback: 0.00
                monto = Decimal("0.00")

        # Crear transacción en estado pending
        transaccion_data = {
            "usuario_id": request.usuario_id,
            "plan_id": request.plan_id,
            "monto": float(monto) if isinstance(monto, Decimal) else monto,
            "status": "pending",
            "provider_metadata": {"simulator": True},
        }

        # Se asume que repository.create_transaccion devuelve un objeto con `id`
        transaccion = await self.repository.create_transaccion(transaccion_data)

        # Generar payment_token para el cliente (MVP: devolver '0' para facilitar pruebas)
        payment_token = "0"

        # Emitir evento transaccion.creada
        try:
            emit_transaccion_creada(
                transaccion_id=getattr(transaccion, "id", None),
                usuario_id=getattr(transaccion, "usuario_id", None),
                plan_id=getattr(transaccion, "plan_id", None),
                monto=str(getattr(transaccion, "monto", monto)),
                status=getattr(transaccion, "status", "pending"),
                created_at=getattr(transaccion, "created_at", datetime.utcnow()),
            )
        except Exception:
            # no romper el flujo por fallos en pubsub
            pass

        return TransaccionCreateResponse(transaccion_id=getattr(transaccion, "id", None), payment_token=payment_token)


class ProcessPaymentNotificationUseCase:
    """Caso de uso: procesar notificación de pago (webhook).

    Flujo:
    - Validar payload
    - Buscar transacción
    - Si ya está procesada (success/failed) respetar idempotencia
    - Interpretar `payment_token` y actualizar la transacción
    - Si success: actualizar/crear suscripción y emitir eventos
    """

    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service

    async def execute(self, payload: PaymentNotificationSchema) -> TransaccionReadSchema:
        # Validar payload
        is_valid, error_msg = validate_payment_notification(payload)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        transaccion_id = payload.transaccion_id

        # Buscar transacción
        transaccion = await self.repository.get_transaccion_by_id(transaccion_id)
        if not transaccion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")

        # Idempotencia: si ya procesada, retornar el estado actual
        if getattr(transaccion, "status", None) in {"success", "failed"}:
            return TransaccionReadSchema(
                transaccion_id=transaccion.id,
                usuario_id=transaccion.usuario_id,
                plan_id=transaccion.plan_id,
                monto=Decimal(str(transaccion.monto)),
                status=transaccion.status,
                provider_metadata=transaccion.provider_metadata,
                created_at=transaccion.created_at,
                updated_at=getattr(transaccion, "updated_at", None),
            )

        # Interpretar token (MVP convention)
        token = payload.payment_token
        success = True if token == "0" else False

        new_status = "success" if success else "failed"

        # Actualizar transacción
        updated = await self.repository.update_transaccion(transaccion_id, {"status": new_status, "provider_metadata": payload.metadata or {}})

        # Emitir evento transaccion.actualizada
        try:
            emit_transaccion_actualizada(
                transaccion_id=updated.id,
                status=updated.status,
                provider_metadata=updated.provider_metadata,
                updated_at=getattr(updated, "updated_at", datetime.utcnow()),
            )
        except Exception:
            pass

        # Si success, crear/actualizar suscripción del usuario
        if success:
            # Asumimos que existe un método en el repository/service para aplicar la transacción a la suscripción
            # Ej: repository.apply_payment_result(transaccion_id) o service.apply_payment(transaccion)
            try:
                sus = await self.service.apply_successful_payment(updated)
                # emitir evento suscripcion.actualizada si el servicio retornó la suscripción
                try:
                    if sus is not None:
                        emit_suscripcion_actualizada(
                            suscripcion_id=getattr(sus, "id", None),
                            usuario_id=getattr(sus, "usuario_id", None),
                            plan_anterior=getattr(sus, "plan_anterior", None),
                            plan_nuevo=getattr(sus, "plan", None),
                            fecha_inicio=getattr(sus, "fecha_inicio", None),
                            fecha_fin=getattr(sus, "fecha_fin", None),
                            transaccion_id=updated.id,
                        )
                except Exception:
                    pass
            except Exception:
                # No fallar el webhook por errores no críticos; registrar y continuar
                pass

        # Construir y retornar TransaccionReadSchema
        return TransaccionReadSchema(
            transaccion_id=updated.id,
            usuario_id=updated.usuario_id,
            plan_id=updated.plan_id,
            monto=Decimal(str(updated.monto)),
            status=updated.status,
            provider_metadata=updated.provider_metadata,
            created_at=updated.created_at,
            updated_at=getattr(updated, "updated_at", None),
        )


class CancelSuscripcionUseCase:
    """Cancelar una suscripción activa. Corresponde a `PATCH /suscripciones/{id}/cancel`."""

    def __init__(self, repository, service):
        self.repository = repository
        self.service = service

    async def execute(self, usuario_id: int, suscripcion_id: int, request: SuscripcionCancelRequest) -> SuscripcionUsuarioReadSchema:
        # validar payload
        is_valid, err = validate_cancel_payload(request)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

        sus = await self.repository.get_by_id(suscripcion_id)
        if not sus:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")

        # ownership check
        if sus.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para cancelar esta suscripción")

        # opcional: delegar a service.can_cancel si existe
        if hasattr(self.service, "can_cancel"):
            can_cancel, reason = await self.service.can_cancel(sus)
            if not can_cancel:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason or "No se puede cancelar")

        update_data = {}
        if request.mode == "immediate":
            update_data["estado_suscripcion"] = "CANCELLED"
            update_data["fecha_fin"] = datetime.utcnow()
            update_data["cancelled_at"] = datetime.utcnow()
        else:
            # end_of_period: mantener hasta fecha_fin actual (no cambios inmediatos)
            update_data["estado_suscripcion"] = "CANCELLATION_SCHEDULED"

        updated = await self.repository.update(sus, update_data)

        # emitir evento de actualización
        try:
            emit_suscripcion_actualizada(
                suscripcion_id=getattr(updated, "id", None),
                usuario_id=getattr(updated, "usuario_id", None),
                plan_anterior=getattr(updated, "plan_anterior", None),
                plan_nuevo=getattr(updated, "plan", None),
                fecha_inicio=getattr(updated, "fecha_inicio", None),
                fecha_fin=getattr(updated, "fecha_fin", None),
                transaccion_id=None,
            )
        except Exception:
            pass

        # retornar representación
        if hasattr(self.service, "build_suscripcion_response"):
            sus_dict = self.service.build_suscripcion_response(updated)
            return SuscripcionUsuarioReadSchema(**sus_dict)
        # si no hay helper, crear manualmente
        return SuscripcionUsuarioReadSchema(
            suscripcion_id=getattr(updated, "id", None),
            plan=getattr(updated, "plan", None),
            estado_suscripcion=getattr(updated, "estado_suscripcion", None),
            fecha_inicio=getattr(updated, "fecha_inicio", None),
            fecha_fin=getattr(updated, "fecha_fin", None),
        )


class AdminAssignSubscriptionUseCase:
    """Asignar un plan manualmente desde un endpoint admin (`POST /admin/suscripciones/assign`)."""

    def __init__(self, repository, service):
        self.repository = repository
        self.service = service

    async def execute(self, request: AdminAssignSubscriptionRequest) -> SuscripcionUsuarioReadSchema:
        is_valid, err = validate_admin_assign_payload(request)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

        # Se asume repository.assign_plan_to_user(usuario_id, plan_id, fecha_inicio, fecha_fin)
        assigned = await self.repository.assign_plan_to_user(
            usuario_id=request.usuario_id,
            plan_id=request.plan_id,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
        )

        # emitir evento
        try:
            emit_suscripcion_actualizada(
                suscripcion_id=getattr(assigned, "id", None),
                usuario_id=getattr(assigned, "usuario_id", None),
                plan_anterior=getattr(assigned, "plan_anterior", None),
                plan_nuevo=getattr(assigned, "plan", None),
                fecha_inicio=getattr(assigned, "fecha_inicio", None),
                fecha_fin=getattr(assigned, "fecha_fin", None),
                transaccion_id=None,
            )
        except Exception:
            pass

        if hasattr(self.service, "build_suscripcion_response"):
            return SuscripcionUsuarioReadSchema(**self.service.build_suscripcion_response(assigned))

        return SuscripcionUsuarioReadSchema(
            suscripcion_id=getattr(assigned, "id", None),
            plan=getattr(assigned, "plan", None),
            estado_suscripcion=getattr(assigned, "estado_suscripcion", None),
            fecha_inicio=getattr(assigned, "fecha_inicio", None),
            fecha_fin=getattr(assigned, "fecha_fin", None),
        )


class TransaccionListUseCase:
    """Listar transacciones de un usuario (`GET /usuarios/{id}/transacciones`)."""

    def __init__(self, repository):
        self.repository = repository

    async def execute(self, usuario_id: int, page: int = 1, per_page: int = 20, is_admin: bool = False) -> dict:
        # si no es admin, forzar usuario_id
        # Se asume repository.list_transacciones(usuario_id, offset, limit) y repository.count_transacciones(usuario_id)
        offset = (page - 1) * per_page
        items = await self.repository.list_transacciones(usuario_id=usuario_id if not is_admin else None, offset=offset, limit=per_page)
        total = await self.repository.count_transacciones(usuario_id=usuario_id if not is_admin else None)

        parsed = []
        for t in items:
            parsed.append(
                TransaccionReadSchema(
                    transaccion_id=getattr(t, "id", None),
                    usuario_id=getattr(t, "usuario_id", None),
                    plan_id=getattr(t, "plan_id", None),
                    monto=Decimal(str(getattr(t, "monto", 0))),
                    status=getattr(t, "status", None),
                    provider_metadata=getattr(t, "provider_metadata", None),
                    created_at=getattr(t, "created_at", None),
                    updated_at=getattr(t, "updated_at", None),
                )
            )

        # Crear respuesta paginada usando el helper central
        return create_paginated_response(
            message="Transacciones obtenidas",
            data=parsed,
            page=page,
            per_page=per_page,
            total_items=total,
        )
