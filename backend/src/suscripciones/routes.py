"""
Rutas FastAPI para gestión de suscripciones.
"""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, status, HTTPException

from ..config.dependencies import get_db, get_current_user, require_admin
from ..auth.models import Usuario
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.base_models import (
    ApiResponse,
    SuccessResponse,
    PaginatedResponse,
    PaginationParams,
    create_paginated_response,
)

from .schemas import (
    CheckoutCreateRequest,
    TransaccionCreateResponse,
    SuscripcionUsuarioReadSchema,
    SuscripcionCancelRequest,
    AdminAssignSubscriptionRequest,
    PlanReadSchema,
)
from .use_cases import (
    ListPlanesUseCase,
    CheckoutCreateUseCase,
    ProcessPaymentNotificationUseCase,
    CancelSuscripcionUseCase,
    AdminAssignSubscriptionUseCase,
    TransaccionListUseCase,
    GetMySuscripcionUseCase,
    ListSuscripcionesUseCase,
    GetSuscripcionByIdUseCase,
)


router = APIRouter()


# ==================== ENDPOINTS ====================

@router.get(
    "/planes",
    response_model=ApiResponse[List[PlanReadSchema]],
    summary="Listar planes disponibles con sus características"
)
async def list_planes(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Lista todos los planes disponibles con sus características.
    
    Devuelve:
    - FREE: Plan gratuito con características básicas
    - PREMIUM: Plan de pago con todas las características
    
    Útil para mostrar en UI de comparación de planes.
    """
    use_case = ListPlanesUseCase()
    planes = await use_case.execute(db)
    return ApiResponse(
        success=True, 
        message="Planes disponibles obtenidos", 
        data=planes
    )


@router.post(
    "/",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Asignar/Crear suscripción (Admin)",
    dependencies=[Depends(require_admin)]
)
async def create_suscripcion(
    request: AdminAssignSubscriptionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Asignar un plan a un usuario (solo admins). Usa el caso de uso de admin."""
    use_case = AdminAssignSubscriptionUseCase()
    assigned = await use_case.execute(db, request)
    return ApiResponse(success=True, message="Suscripción asignada", data=assigned)


@router.get(
    "/me",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    summary="Obtener mi suscripción activa"
)
async def get_my_suscripcion(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Obtiene la suscripción activa del usuario autenticado."""
    use_case = GetMySuscripcionUseCase()
    suscripcion = await use_case.execute(db, int(current_user.id))
    return ApiResponse(success=True, message="Suscripción activa obtenida", data=suscripcion)


@router.get(
    "/",
    response_model=PaginatedResponse[SuscripcionUsuarioReadSchema],
    summary="Listar suscripciones"
)
async def list_suscripciones(
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Lista suscripciones: usuarios ven las suyas, admins ven todas (paginado)."""
    is_admin = getattr(current_user, 'rol', None) == "admin"
    
    use_case = ListSuscripcionesUseCase()
    result = await use_case.execute(
        session=db,
        usuario_id=int(current_user.id),
        page=pagination.page,
        per_page=pagination.per_page,
        is_admin=is_admin
    )
    
    return result


@router.get(
    "/stats",
    response_model=ApiResponse[dict],
    summary="Estadísticas de suscripciones (Admin)",
    dependencies=[Depends(require_admin)]
)
async def get_suscripcion_stats(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Estadísticas ligeras (implementación simple)."""
    # Implementación mínima: contar suscripciones y total ingresos (si existe campo precio en suscripciones)
    total_sql = "SELECT COUNT(*) FROM suscripciones_usuario"
    total = int((await db.execute(total_sql)).scalar() or 0)
    return ApiResponse(success=True, message="Stats", data={"total_suscripciones": total})


@router.get(
    "/{suscripcion_id}",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    summary="Obtener suscripción por ID"
)
async def get_suscripcion(
    suscripcion_id: int,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Obtiene una suscripción por ID con control de acceso."""
    is_admin = getattr(current_user, 'rol', None) == 'admin'
    
    use_case = GetSuscripcionByIdUseCase()
    suscripcion = await use_case.execute(
        session=db,
        suscripcion_id=suscripcion_id,
        current_user_id=int(current_user.id),
        is_admin=is_admin
    )
    
    return ApiResponse(success=True, message="Suscripción obtenida", data=suscripcion)


@router.post(
    "/upgrade",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    summary="Upgrade de FREE a PREMIUM (simulado para MVP)"
)
async def upgrade_to_premium(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Simula un upgrade de FREE a PREMIUM para el usuario autenticado.
    
    Flujo MVP (sin pasarela real):
    1. Verifica que el usuario tenga plan FREE
    2. Busca el plan PREMIUM en BD
    3. Asigna el plan PREMIUM al usuario
    4. Actualiza la suscripción a PREMIUM
    
    Validaciones:
    - Solo usuarios con plan FREE pueden hacer upgrade
    - No se puede downgrade de PREMIUM a FREE por este endpoint
    
    En producción esto sería reemplazado por el flujo de checkout + webhook.
    """
    from .repositories import SuscripcionRepository
    from .services import SuscripcionService
    
    repo = SuscripcionRepository(db)
    service = SuscripcionService()
    
    # Obtener suscripción actual
    suscripcion_actual = await repo.get_by_usuario_id(int(current_user.id))
    
    if not suscripcion_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una suscripción activa"
        )
    
    # Verificar que sea plan FREE
    plan_nombre = suscripcion_actual.plan.nombre_plan.upper()
    if plan_nombre != "FREE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "upgrade_not_allowed",
                "message": f"Ya tienes un plan {plan_nombre}. Solo puedes hacer upgrade desde FREE.",
                "current_plan": plan_nombre
            }
        )
    
    # Buscar plan PREMIUM
    from sqlalchemy import select, func
    from .models import Plan
    
    stmt = select(Plan).where(func.upper(Plan.nombre_plan) == "PREMIUM")
    result = await db.execute(stmt)
    plan_premium = result.scalars().first()
    
    if not plan_premium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan PREMIUM no encontrado. Ejecuta el seed de planes."
        )
    
    # Asignar plan PREMIUM
    suscripcion_upgraded = await repo.assign_plan_to_user(
        usuario_id=int(current_user.id),
        plan_id=plan_premium.id,
        fecha_inicio=None,  # Usa fecha actual
        fecha_fin=None  # Premium sin límite por ahora (en producción calcular según periodo)
    )
    
    # Construir respuesta
    response_data = service.build_suscripcion_response(suscripcion_upgraded)
    
    return ApiResponse(
        success=True, 
        message="¡Bienvenido a Premium! Upgrade completado exitosamente (simulado)",
        data=SuscripcionUsuarioReadSchema(**response_data)
    )


@router.post(
    "/{suscripcion_id}/cancel",
    response_model=SuccessResponse[None],
    summary="Cancelar suscripción PREMIUM"
)
async def cancel_suscripcion(
    suscripcion_id: int,
    request: SuscripcionCancelRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Cancela una suscripción PREMIUM (downgrade a FREE).
    
    Validaciones:
    - Solo se pueden cancelar suscripciones PREMIUM
    - Usuarios FREE no tienen nada que cancelar (ya es el plan base)
    - El usuario debe ser dueño de la suscripción o admin
    
    Parámetros:
    - mode: 'immediate' (cancela ahora) o 'end_of_period' (al final del periodo)
    - reason: Motivo opcional de cancelación
    
    Resultado:
    - Si mode='immediate': downgrade inmediato a FREE
    - Si mode='end_of_period': marca para cancelar al final del periodo
    """
    from .repositories import SuscripcionRepository
    
    repo = SuscripcionRepository(db)
    
    # Obtener la suscripción
    suscripcion = await repo.get_by_id(suscripcion_id)
    
    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suscripción no encontrada"
        )
    
    # Verificar ownership (o admin)
    is_admin = getattr(current_user, 'rol', None) == 'admin'
    if not is_admin and suscripcion.usuario_id != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta suscripción"
        )
    
    # Verificar que sea plan PREMIUM
    plan_nombre = suscripcion.plan.nombre_plan.upper()
    if plan_nombre == "FREE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "cannot_cancel_free_plan",
                "message": "No puedes cancelar el plan FREE. Ya tienes el plan base gratuito.",
                "suggestion": "Si quieres upgrade a Premium, usa POST /api/suscripciones/upgrade"
            }
        )
    
    # El mode ya fue validado por Pydantic (enum CancelMode)
    # Ejecutar la cancelación
    use_case = CancelSuscripcionUseCase()
    await use_case.execute(db, int(current_user.id), suscripcion_id, request)
    
    return SuccessResponse(
        message=f"Suscripción PREMIUM cancelada exitosamente (modo: {request.mode.value})",
        data=None
    )


@router.post(
    "/renew",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    summary="Renovar suscripción Premium"
)
async def renew_suscripcion(
    request: dict,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Placeholder para renovar: en este repositorio la renovación se maneja vía asignar plan o pago."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Renew endpoint not implemented in this version")

@router.post(
    "/checkout",
    response_model=ApiResponse[TransaccionCreateResponse],
    summary="[PASO 1] Iniciar checkout - Crear transacción de pago"
)
async def create_checkout(
    request: CheckoutCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    PASO 1 del flujo de pago: Crear transacción en estado 'pending'.
    
    Flujo completo de upgrade FREE → PREMIUM:
    
    1️⃣ POST /api/suscripciones/checkout (ESTE ENDPOINT)
       - Crea transacción en estado 'pending'
       - Devuelve transaccion_id y payment_token
       - El frontend usa payment_token para simular pago
    
    2️⃣ [FRONTEND] Simula pago con payment_token
       - '0' = pago exitoso
       - '1' = pago fallido
       - Otro = pago pendiente
    
    3️⃣ POST /api/suscripciones/payments/webhook
       - Procesa el resultado del pago
       - Si exitoso: actualiza transacción y asigna plan PREMIUM
       - Si fallido: marca transacción como 'failed'
    
    Request Body:
    {
        "usuario_id": 1,
        "plan_id": 2,  // ID del plan PREMIUM
        "monto": 9.99,
        "payment_method": "tarjeta",
        "metadata": { "campania": "promo_octubre" }
    }
    
    Response:
    {
        "success": true,
        "data": {
            "transaccion_id": 123,
            "payment_token": "a1b2c3d4..."  // Usar en webhook
        }
    }
    """
    use_case = CheckoutCreateUseCase()
    resp = await use_case.execute(db, request)
    return ApiResponse(
        success=True, 
        message="Checkout creado. Usa payment_token para simular pago en el webhook.",
        data=resp
    )


@router.post(
    "/payments/webhook",
    response_model=ApiResponse[dict],
    summary="[PASO 2] Webhook de notificación de pago (simula respuesta de pasarela)"
)
async def payments_webhook(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    PASO 2 del flujo de pago: Procesar resultado de la pasarela (simulado).
    
    Flujo:
    1. Recibe transaccion_id y payment_token del frontend
    2. Valida el payment_token:
       - '0' → pago SUCCESS (asigna plan PREMIUM)
       - '1' → pago FAILED (marca transacción fallida)
       - Otro → deja en PENDING
    3. Si SUCCESS: actualiza suscripción del usuario a PREMIUM
    4. Emite eventos de negocio (analytics, notificaciones)
    
    Request Body (PaymentNotificationSchema):
    {
        "transaccion_id": 123,
        "payment_token": "0",  // "0" = success, "1" = failed
        "metadata": {
            "payment_method": "tarjeta",
            "card_last4": "4242"
        }
    }
    
    Response exitoso:
    {
        "success": true,
        "message": "Pago procesado exitosamente. Usuario actualizado a PREMIUM",
        "data": {
            "transaccion_id": 123,
            "status": "success",
            "plan_asignado": "PREMIUM"
        }
    }
    
    Response fallido:
    {
        "success": true,
        "message": "Pago fallido. Transacción marcada como failed",
        "data": {
            "transaccion_id": 123,
            "status": "failed"
        }
    }
    
    NOTA: En producción, este endpoint sería llamado por Stripe/PayPal/MercadoPago
    con firma HMAC para validar autenticidad. En MVP se simula.
    """
    # Esperamos un payload compatible con PaymentNotificationSchema
    use_case = ProcessPaymentNotificationUseCase()
    updated = await use_case.execute(db, payload)
    
    # Determinar mensaje según status
    status_msg = {
        "success": "Pago procesado exitosamente. Usuario actualizado a PREMIUM",
        "failed": "Pago fallido. Transacción marcada como rechazada",
        "pending": "Pago en procesamiento. Transacción pendiente de confirmación"
    }.get(getattr(updated, 'status', 'pending'), "Webhook procesado")
    
    return ApiResponse(
        success=True, 
        message=status_msg,
        data={
            "transaccion_id": getattr(updated, 'transaccion_id', None),
            "status": getattr(updated, 'status', 'pending')
        }
    )
