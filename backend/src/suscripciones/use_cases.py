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
from datetime import datetime, timezone
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
    PlanesRepository,
)
from .services import SuscripcionService

# Usar la paginación centralizada
from ..shared.base_models import create_paginated_response

# Eventos (se espera que exista `src/suscripciones/events.py` con estos helpers)
from .events import (
    emit_transaccion_creada,
    emit_transaccion_actualizada,
    emit_suscripcion_actualizada,
)

logger = logging.getLogger(__name__)


class ListPlanesUseCase:
    """Lista los planes disponibles (`GET /planes`)."""
    async def execute(self, session: AsyncSession) -> list[PlanReadSchema]:
        logger.debug("ListPlanesUseCase.execute: iniciando listado de planes")
        try:
            planes_repo = PlanesRepository(session)
            planes = await planes_repo.list_planes()
            result = []
            for p in planes:
                nombre = p.get("nombre_plan") if isinstance(p, dict) else getattr(p, "nombre_plan", None)
                precio = p.get("precio") if isinstance(p, dict) else getattr(p, "precio", None)
                periodo = p.get("periodo_facturacion") if isinstance(p, dict) else getattr(p, "periodo_facturacion", None)
                caracteristicas = p.get("caracteristicas", []) if isinstance(p, dict) else getattr(p, "caracteristicas", [])
                result.append(
                    PlanReadSchema(
                        id=p.get("id") if isinstance(p, dict) else getattr(p, "id", None),
                        nombre_plan=nombre,
                        precio=Decimal(str(precio)) if precio is not None else Decimal("0.00"),
                        periodo_facturacion=periodo or "",
                        caracteristicas=caracteristicas,
                    )
                )

            logger.info("ListPlanesUseCase.execute: obtenido %d planes", len(result))
            logger.debug("ListPlanesUseCase.execute: planes=%s", result)
            return result
        except Exception as e:
            logger.exception("ListPlanesUseCase.execute: error inesperado al listar planes: %s", e)
            raise HTTPException(status_code=500, detail="Error interno al listar planes")


class CheckoutCreateUseCase:
    """Iniciar checkout: crear transacción en estado pending y devolver payment_token."""
    async def execute(self, session: AsyncSession, request: CheckoutCreateRequest) -> TransaccionCreateResponse:
        logger.debug("CheckoutCreateUseCase.execute: inicio checkout usuario=%s plan=%s", request.usuario_id, request.plan_id)
        try:
            is_valid, error_msg = validate_checkout_payload(request)
            if not is_valid:
                logger.warning("CheckoutCreateUseCase.execute: payload inválido: %s", error_msg)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

            repository = SuscripcionRepository(session)
            service = SuscripcionService()

            plan = await repository.get_plan_by_id(request.plan_id)
            if not plan:
                logger.warning("CheckoutCreateUseCase.execute: plan no encontrado id=%s", request.plan_id)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")

            monto = request.monto
            if monto is None:
                monto = getattr(plan, "precio", None)
                if monto is None:
                    monto = Decimal("0.00")

            transaccion_data = {
                "usuario_id": request.usuario_id,
                "plan_id": request.plan_id,
                "monto": float(monto) if isinstance(monto, Decimal) else monto,
                "status": "pending",
                "provider_metadata": {"simulator": True},
            }

            transaccion = await repository.create_transaccion(transaccion_data)

            payment_token = "0"

            try:
                await emit_transaccion_creada(
                    transaccion_id=getattr(transaccion, "id", None),
                    usuario_id=getattr(transaccion, "usuario_id", None),
                    plan_id=getattr(transaccion, "plan_id", None),
                    monto=str(getattr(transaccion, "monto", monto)),
                    status=getattr(transaccion, "status", "pending"),
                    created_at=getattr(transaccion, "created_at", datetime.now(timezone.utc)),
                )
            except Exception:
                # no romper el flujo por fallos en pubsub
                logger.warning("CheckoutCreateUseCase.execute: fallo emitiendo evento transaccion creada, se ignora")

            logger.info("CheckoutCreateUseCase.execute: transaccion creada id=%s usuario=%s", getattr(transaccion, "id", None), getattr(transaccion, "usuario_id", None))
            logger.debug("CheckoutCreateUseCase.execute: transaccion_data=%s", transaccion_data)

            return TransaccionCreateResponse(transaccion_id=getattr(transaccion, "id", None), payment_token=payment_token)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("CheckoutCreateUseCase.execute: error inesperado: %s", e)
            raise HTTPException(status_code=500, detail="Error interno al crear checkout")


class ProcessPaymentNotificationUseCase:
    """Procesar notificación de pago (webhook)."""
    async def execute(self, session: AsyncSession, payload: PaymentNotificationSchema) -> TransaccionReadSchema:
        logger.debug("ProcessPaymentNotificationUseCase.execute: procesando payload=%s", payload)
        try:
            is_valid, error_msg = validate_payment_notification(payload)
            if not is_valid:
                logger.warning("ProcessPaymentNotificationUseCase.execute: payload inválido: %s", error_msg)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

            repository = SuscripcionRepository(session)
            service = SuscripcionService()

            transaccion_id = payload.transaccion_id
            transaccion = await repository.get_transaccion_by_id(transaccion_id)
            if not transaccion:
                logger.warning("ProcessPaymentNotificationUseCase.execute: transacción no encontrada id=%s", transaccion_id)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")

            if getattr(transaccion, "status", None) in {"success", "failed"}:
                logger.info("ProcessPaymentNotificationUseCase.execute: transacción ya procesada id=%s status=%s", transaccion_id, transaccion.status)
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

            token = payload.payment_token
            success = True if token == "0" else False
            new_status = "success" if success else "failed"

            updated = await repository.update_transaccion(transaccion_id, {"status": new_status, "provider_metadata": payload.metadata or {}})

            try:
                await emit_transaccion_actualizada(
                    transaccion_id=updated.id,
                    status=updated.status,
                    provider_metadata=updated.provider_metadata,
                    updated_at=getattr(updated, "updated_at", datetime.now(timezone.utc)),
                )
            except Exception:
                logger.warning("ProcessPaymentNotificationUseCase.execute: fallo emitiendo evento transaccion actualizada, se ignora")

            if success:
                try:
                    # delegar comportamiento al service si existe (async)
                    if hasattr(service, "apply_successful_payment"):
                        sus = await service.apply_successful_payment(updated, repository)
                    else:
                        sus = None

                    try:
                        if sus is not None:
                            await emit_suscripcion_actualizada(
                                suscripcion_id=getattr(sus, "id", None),
                                usuario_id=getattr(sus, "usuario_id", None),
                                plan_anterior=getattr(sus, "plan_anterior", None),
                                plan_nuevo=getattr(sus, "plan", None),
                                fecha_inicio=getattr(sus, "fecha_inicio", None),
                                fecha_fin=getattr(sus, "fecha_fin", None),
                                transaccion_id=updated.id,
                            )
                    except Exception:
                        logger.warning("ProcessPaymentNotificationUseCase.execute: fallo emitiendo evento suscripcion actualizada, se ignora")
                except Exception as e:
                    # No fallar el webhook por errores no críticos
                    logger.error("ProcessPaymentNotificationUseCase.execute: error aplicando pago exitoso: %s", e)

            logger.info("ProcessPaymentNotificationUseCase.execute: transaccion procesada id=%s status=%s", updated.id, updated.status)

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
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("ProcessPaymentNotificationUseCase.execute: error inesperado: %s", e)
            raise HTTPException(status_code=500, detail="Error interno procesando notificación de pago")


class CancelSuscripcionUseCase:
    """Cancelar una suscripción activa."""
    async def execute(self, session: AsyncSession, usuario_id: int, suscripcion_id: int, request: SuscripcionCancelRequest) -> SuscripcionUsuarioReadSchema:
        logger.debug("CancelSuscripcionUseCase.execute: usuario=%s suscripcion=%s modo=%s", usuario_id, suscripcion_id, getattr(request, 'mode', None))
        try:
            is_valid, err = validate_cancel_payload(request)
            if not is_valid:
                logger.warning("CancelSuscripcionUseCase.execute: payload inválido: %s", err)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

            repository = SuscripcionRepository(session)
            service = SuscripcionService()

            sus = await repository.get_by_id(suscripcion_id)
            if not sus:
                logger.warning("CancelSuscripcionUseCase.execute: suscripción no encontrada id=%s", suscripcion_id)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")

            if sus.usuario_id != usuario_id:
                logger.warning("CancelSuscripcionUseCase.execute: intento de cancelación sin permiso usuario=%s suscripcion=%s", usuario_id, suscripcion_id)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para cancelar esta suscripción")

            if hasattr(service, "can_cancel"):
                can_cancel, reason = service.can_cancel(sus)
                if not can_cancel:
                    logger.info("CancelSuscripcionUseCase.execute: cancelación no permitida por service: %s", reason)
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason or "No se puede cancelar")

            update_data = {}
            if request.mode == "immediate":
                update_data["estado_suscripcion"] = "CANCELLED"
                update_data["fecha_fin"] = datetime.now(timezone.utc)
                update_data["cancelled_at"] = datetime.now(timezone.utc)
            else:
                update_data["estado_suscripcion"] = "CANCELLATION_SCHEDULED"

            updated = await repository.update(sus, update_data)

            try:
                await emit_suscripcion_actualizada(
                    suscripcion_id=getattr(updated, "id", None),
                    usuario_id=getattr(updated, "usuario_id", None),
                    plan_anterior=getattr(updated, "plan_anterior", None),
                    plan_nuevo=getattr(updated, "plan", None),
                    fecha_inicio=getattr(updated, "fecha_inicio", None),
                    fecha_fin=getattr(updated, "fecha_fin", None),
                    transaccion_id=None,
                )
            except Exception:
                logger.warning("CancelSuscripcionUseCase.execute: fallo emitiendo evento suscripcion actualizada, se ignora")

            if hasattr(service, "build_suscripcion_response"):
                sus_dict = service.build_suscripcion_response(updated)
                logger.info("CancelSuscripcionUseCase.execute: suscripción actualizada id=%s", getattr(updated, "id", None))
                return SuscripcionUsuarioReadSchema(**sus_dict)

            logger.info("CancelSuscripcionUseCase.execute: suscripción actualizada id=%s", getattr(updated, "id", None))
            return SuscripcionUsuarioReadSchema(
                suscripcion_id=getattr(updated, "id", None),
                plan=getattr(updated, "plan", None),
                estado_suscripcion=getattr(updated, "estado_suscripcion", None),
                fecha_inicio=getattr(updated, "fecha_inicio", None),
                fecha_fin=getattr(updated, "fecha_fin", None),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("CancelSuscripcionUseCase.execute: error inesperado: %s", e)
            raise HTTPException(status_code=500, detail="Error interno al cancelar suscripción")


class AdminAssignSubscriptionUseCase:
    """Asignar un plan manualmente desde admin."""
    async def execute(self, session: AsyncSession, request: AdminAssignSubscriptionRequest) -> SuscripcionUsuarioReadSchema:
        logger.debug("AdminAssignSubscriptionUseCase.execute: asignando plan admin usuario=%s plan=%s", request.usuario_id, request.plan_id)
        try:
            is_valid, err = validate_admin_assign_payload(request)
            if not is_valid:
                logger.warning("AdminAssignSubscriptionUseCase.execute: payload inválido: %s", err)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

            repository = SuscripcionRepository(session)
            service = SuscripcionService()

            assigned = await repository.assign_plan_to_user(
                usuario_id=request.usuario_id,
                plan_id=request.plan_id,
                fecha_inicio=request.fecha_inicio,
                fecha_fin=request.fecha_fin,
            )

            try:
                await emit_suscripcion_actualizada(
                    suscripcion_id=getattr(assigned, "id", None),
                    usuario_id=getattr(assigned, "usuario_id", None),
                    plan_anterior=getattr(assigned, "plan_anterior", None),
                    plan_nuevo=getattr(assigned, "plan", None),
                    fecha_inicio=getattr(assigned, "fecha_inicio", None),
                    fecha_fin=getattr(assigned, "fecha_fin", None),
                    transaccion_id=None,
                )
            except Exception:
                logger.warning("AdminAssignSubscriptionUseCase.execute: fallo emitiendo evento suscripcion actualizada, se ignora")

            if hasattr(service, "build_suscripcion_response"):
                resp = service.build_suscripcion_response(assigned)
                logger.info("AdminAssignSubscriptionUseCase.execute: asignación completada id=%s usuario=%s", getattr(assigned, "id", None), getattr(assigned, "usuario_id", None))
                return SuscripcionUsuarioReadSchema(**resp)

            logger.info("AdminAssignSubscriptionUseCase.execute: asignación completada id=%s usuario=%s", getattr(assigned, "id", None), getattr(assigned, "usuario_id", None))
            return SuscripcionUsuarioReadSchema(
                suscripcion_id=getattr(assigned, "id", None),
                plan=getattr(assigned, "plan", None),
                estado_suscripcion=getattr(assigned, "estado_suscripcion", None),
                fecha_inicio=getattr(assigned, "fecha_inicio", None),
                fecha_fin=getattr(assigned, "fecha_fin", None),
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("AdminAssignSubscriptionUseCase.execute: error inesperado: %s", e)
            raise HTTPException(status_code=500, detail="Error interno asignando suscripción")


class TransaccionListUseCase:
    """Listar transacciones de un usuario (`GET /usuarios/{id}/transacciones`)."""

    async def execute(self, session: AsyncSession, usuario_id: int, page: int = 1, per_page: int = 20, is_admin: bool = False) -> dict:
        logger.debug("TransaccionListUseCase.execute: usuario=%s page=%d per_page=%d is_admin=%s", usuario_id, page, per_page, is_admin)
        try:
            offset = (page - 1) * per_page
            repository = SuscripcionRepository(session)
            items = await repository.list_transacciones(usuario_id=usuario_id if not is_admin else None, offset=offset, limit=per_page)
            total = await repository.count_transacciones(usuario_id=usuario_id if not is_admin else None)

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

            logger.info("TransaccionListUseCase.execute: retornando %d transacciones (total=%d)", len(parsed), total)
            logger.debug("TransaccionListUseCase.execute: transacciones=%s", parsed)

            return create_paginated_response(
                message="Transacciones obtenidas",
                data=parsed,
                page=page,
                per_page=per_page,
                total_items=total,
            )
        except Exception as e:
            logger.exception("TransaccionListUseCase.execute: error inesperado: %s", e)
            raise HTTPException(status_code=500, detail="Error interno obteniendo transacciones")
