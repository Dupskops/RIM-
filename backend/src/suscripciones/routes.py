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

from .repositories import SuscripcionRepository, PlanesRepository
from .services import SuscripcionService
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
)


router = APIRouter()


# ==================== DEPENDENCIES ====================

async def get_suscripcion_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> SuscripcionRepository:
    """Inyección de dependencia del repositorio de suscripciones."""
    return SuscripcionRepository(db)


def get_suscripcion_service() -> SuscripcionService:
    """Inyección de dependencia del servicio de suscripciones."""
    return SuscripcionService()


# ==================== ENDPOINTS ====================

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
    """Obtiene la suscripción activa del usuario autenticado (la más reciente)."""
    repo = SuscripcionRepository(db)
    svc = SuscripcionService()

    # Buscar la suscripción más reciente del usuario
    stmt = await db.execute(
        "SELECT id FROM suscripciones_usuario WHERE usuario_id = :uid ORDER BY id DESC LIMIT 1",
        {"uid": int(current_user.id)},
    )
    row = stmt.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    sus_id = row[0]
    sus = await repo.get_by_id(sus_id)
    if not sus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    data = svc.build_suscripcion_response(sus)
    return ApiResponse(success=True, message="Suscripción activa obtenida", data=data)


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
    """Lista suscripciones simples: usuarios ven las suyas, admins ven todas (paginado).
    Nota: implementación ligera que puede reemplazarse por un use case más completo.
    """
    is_admin = getattr(current_user, 'rol', None) == "admin"
    repo = SuscripcionRepository(db)
    svc = SuscripcionService()

    offset = (pagination.page - 1) * pagination.per_page
    limit = pagination.per_page

    sql = "SELECT id FROM suscripciones_usuario "
    params = {}
    if not is_admin:
        sql += "WHERE usuario_id = :uid "
        params["uid"] = int(current_user.id)
    sql += "ORDER BY id DESC LIMIT :limit OFFSET :offset"
    params.update({"limit": limit, "offset": offset})

    res = await db.execute(sql, params)
    rows = res.fetchall()
    sus_list = []
    for r in rows:
        s = await repo.get_by_id(r[0])
        if s:
            sus_list.append(svc.build_suscripcion_response(s))

    total = 0
    count_sql = "SELECT COUNT(*) FROM suscripciones_usuario"
    if not is_admin:
        count_sql += " WHERE usuario_id = :uid"
        cnt_res = await db.execute(count_sql, {"uid": int(current_user.id)})
    else:
        cnt_res = await db.execute(count_sql)
    total = int(cnt_res.scalar() or 0)

    return create_paginated_response(message="Suscripciones obtenidas", data=sus_list, page=pagination.page, per_page=pagination.per_page, total_items=total)


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
    """Obtiene una suscripción por ID con control simple de acceso."""
    repo = SuscripcionRepository(db)
    svc = SuscripcionService()
    sus = await repo.get_by_id(suscripcion_id)
    if not sus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suscripción no encontrada")
    if sus.usuario_id != int(current_user.id) and getattr(current_user, 'rol', None) != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
    data = svc.build_suscripcion_response(sus)
    return ApiResponse(success=True, message="Suscripción obtenida", data=data)


@router.post(
    "/upgrade",
    response_model=ApiResponse[SuscripcionUsuarioReadSchema],
    summary="Upgrade a Premium"
)
async def upgrade_to_premium(
    request: dict,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Endpoint placeholder para upgrade — redirige a admin assign o al flujo de checkout según implementación."""
    # Por simplicidad, redirigimos a AdminAssignSubscriptionUseCase si el request contiene usuario_id
    if 'usuario_id' in request:
        use_case = AdminAssignSubscriptionUseCase()
        assigned = await use_case.execute(db, AdminAssignSubscriptionRequest(**request))
        return ApiResponse(success=True, message="Upgrade asignado", data=assigned)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload no soportado para upgrade en este endpoint")


@router.post(
    "/{suscripcion_id}/cancel",
    response_model=SuccessResponse[None],
    summary="Cancelar suscripción"
)
async def cancel_suscripcion(
    suscripcion_id: int,
    request: SuscripcionCancelRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancela una suscripción especificada (usuario o admin)."""
    use_case = CancelSuscripcionUseCase()
    await use_case.execute(db, int(current_user.id), suscripcion_id, request)
    return SuccessResponse(message="Suscripción cancelada exitosamente", data=None)


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
    summary="Iniciar checkout / crear transacción"
)
async def create_checkout(
    request: CheckoutCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    use_case = CheckoutCreateUseCase()
    resp = await use_case.execute(db, request)
    return ApiResponse(success=True, message="Checkout creado", data=resp)


@router.post(
    "/payments/webhook",
    response_model=ApiResponse[dict],
    summary="Webhook de notificación de pago"
)
async def payments_webhook(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Esperamos un payload compatible con PaymentNotificationSchema
    use_case = ProcessPaymentNotificationUseCase()
    updated = await use_case.execute(db, payload)
    return ApiResponse(success=True, message="Webhook procesado", data={"transaccion_id": getattr(updated, 'transaccion_id', None)})
