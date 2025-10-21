"""
Rutas FastAPI para gestión de suscripciones.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status

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

from .repositories import SuscripcionRepository
from .services import SuscripcionService
from .schemas import (
    CreateSuscripcionRequest,
    UpdateSuscripcionRequest,
    UpgradeToPremiumRequest,
    CancelSuscripcionRequest,
    RenewSuscripcionRequest,
    SuscripcionFilterParams,
    SuscripcionResponse,
    SuscripcionStatsResponse,
)
from .use_cases import (
    CreateSuscripcionUseCase,
    GetSuscripcionUseCase,
    GetActiveSuscripcionUseCase,
    ListSuscripcionesUseCase,
    UpgradeToPremiumUseCase,
    CancelSuscripcionUseCase,
    RenewSuscripcionUseCase,
    GetSuscripcionStatsUseCase
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
    response_model=ApiResponse[SuscripcionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear suscripción (Admin)",
    dependencies=[Depends(require_admin)]
)
async def create_suscripcion(
    request: CreateSuscripcionRequest,
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Crea una nueva suscripción (solo admins).
    
    - **usuario_id**: ID del usuario
    - **plan**: Tipo de plan (freemium/premium)
    - **duracion_meses**: Duración en meses (solo premium, 1-24)
    - **precio**: Precio del plan (obligatorio para premium)
    - **metodo_pago**: Método de pago (obligatorio para premium)
    - **transaction_id**: ID de transacción (obligatorio para premium)
    - **auto_renovacion**: Auto-renovación automática
    - **notas**: Notas adicionales
    """
    use_case = CreateSuscripcionUseCase(repository, service)
    suscripcion = await use_case.execute(request)
    return ApiResponse(
        success=True,
        message="Suscripción creada exitosamente",
        data=suscripcion
    )


@router.get(
    "/me",
    response_model=ApiResponse[SuscripcionResponse],
    summary="Obtener mi suscripción activa"
)
async def get_my_suscripcion(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Obtiene la suscripción activa del usuario autenticado.
    """
    use_case = GetActiveSuscripcionUseCase(repository, service)
    suscripcion = await use_case.execute(str(current_user.id))
    return ApiResponse(
        success=True,
        message="Suscripción activa obtenida",
        data=suscripcion
    )


@router.get(
    "/",
    response_model=PaginatedResponse[SuscripcionResponse],
    summary="Listar suscripciones"
)
async def list_suscripciones(
    filters: Annotated[SuscripcionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Lista suscripciones con filtros y paginación.
    
    - **Usuarios normales**: Solo ven sus propias suscripciones
    - **Admins**: Pueden ver todas las suscripciones y filtrar por usuario
    
    Filtros disponibles:
    - **usuario_id**: ID del usuario (solo admins)
    - **plan**: Tipo de plan (freemium/premium)
    - **status**: Estado (active/cancelled/expired/pending)
    - **activas_only**: Solo suscripciones activas
    - **page**: Número de página (default: 1)
    - **per_page**: Tamaño de página (default: 20, max: 100)
    - **order_by**: Campo para ordenar (id, created_at, start_date, end_date)
    - **order_direction**: Dirección (asc, desc)
    """
    is_admin = getattr(current_user, 'rol', None) == "admin"
    use_case = ListSuscripcionesUseCase(repository, service)
    suscripciones, total = await use_case.execute(filters, pagination, str(current_user.id), is_admin)
    
    return create_paginated_response(
        message="Suscripciones obtenidas exitosamente",
        data=suscripciones,
        page=pagination.page,
        per_page=pagination.per_page,
        total_items=total
    )


@router.get(
    "/stats",
    response_model=ApiResponse[SuscripcionStatsResponse],
    summary="Estadísticas de suscripciones (Admin)",
    dependencies=[Depends(require_admin)]
)
async def get_suscripcion_stats(
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)]
):
    """
    Obtiene estadísticas de suscripciones (solo admins).
    
    Incluye:
    - Total de suscripciones registradas
    - Suscripciones activas
    - Suscripciones freemium
    - Suscripciones premium
    - Ingresos totales
    - Tasa de conversión (% freemium → premium)
    """
    use_case = GetSuscripcionStatsUseCase(repository)
    stats = await use_case.execute()
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=stats
    )


@router.get(
    "/{suscripcion_id}",
    response_model=ApiResponse[SuscripcionResponse],
    summary="Obtener suscripción por ID"
)
async def get_suscripcion(
    suscripcion_id: int,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Obtiene una suscripción por ID.
    
    - **Usuarios normales**: Solo pueden ver sus propias suscripciones
    - **Admins**: Pueden ver cualquier suscripción
    """
    is_admin = getattr(current_user, 'rol', None) == "admin"
    use_case = GetSuscripcionUseCase(repository, service)
    suscripcion = await use_case.execute(suscripcion_id, str(current_user.id), is_admin)
    return ApiResponse(
        success=True,
        message="Suscripción obtenida exitosamente",
        data=suscripcion
    )


@router.post(
    "/upgrade",
    response_model=ApiResponse[SuscripcionResponse],
    summary="Upgrade a Premium"
)
async def upgrade_to_premium(
    request: UpgradeToPremiumRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Realiza upgrade de freemium a premium.
    
    - **duracion_meses**: Duración en meses (1-24)
    - **precio**: Precio del plan (> 0)
    - **metodo_pago**: Método de pago (tarjeta, paypal, transferencia, mercadopago, stripe)
    - **transaction_id**: ID de transacción del pago (único)
    - **auto_renovacion**: Si se renueva automáticamente
    """
    use_case = UpgradeToPremiumUseCase(repository, service)
    suscripcion = await use_case.execute(str(current_user.id), request)
    return ApiResponse(
        success=True,
        message="Upgrade a premium realizado exitosamente",
        data=suscripcion
    )


@router.post(
    "/cancel",
    response_model=SuccessResponse[None],
    summary="Cancelar suscripción"
)
async def cancel_suscripcion(
    request: CancelSuscripcionRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Cancela la suscripción activa del usuario.
    
    - **razon**: Razón de cancelación (opcional)
    """
    use_case = CancelSuscripcionUseCase(repository, service)
    await use_case.execute(str(current_user.id), request)
    return SuccessResponse(
        message="Suscripción cancelada exitosamente",
        data=None
    )


@router.post(
    "/renew",
    response_model=ApiResponse[SuscripcionResponse],
    summary="Renovar suscripción Premium"
)
async def renew_suscripcion(
    request: RenewSuscripcionRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[SuscripcionRepository, Depends(get_suscripcion_repository)],
    service: Annotated[SuscripcionService, Depends(get_suscripcion_service)]
):
    """
    Renueva la suscripción premium del usuario.
    
    - **duracion_meses**: Duración en meses (1-24)
    - **precio**: Precio del plan (> 0)
    - **transaction_id**: ID de transacción del pago (único)
    
    La nueva fecha de fin se calcula desde:
    - La fecha de fin actual (si aún no expiró)
    - La fecha actual (si ya expiró)
    """
    use_case = RenewSuscripcionUseCase(repository, service)
    suscripcion = await use_case.execute(str(current_user.id), request)
    return ApiResponse(
        success=True,
        message="Suscripción renovada exitosamente",
        data=suscripcion
    )
