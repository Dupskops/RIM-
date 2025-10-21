"""
Rutas FastAPI para gestión de motos.
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
    create_paginated_response
)
from .repositories import MotoRepository
from .services import MotoService
from .schemas import (
    RegisterMotoRequest,
    UpdateMotoRequest,
    UpdateKilometrajeRequest,
    MotoFilterParams,
    MotoResponse,
    MotoStatsResponse
)
from .use_cases import (
    RegisterMotoUseCase,
    GetMotoUseCase,
    ListMotosUseCase,
    UpdateMotoUseCase,
    DeleteMotoUseCase,
    UpdateKilometrajeUseCase,
    GetMotoStatsUseCase
)


router = APIRouter()


# ==================== DEPENDENCIES ====================

async def get_moto_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MotoRepository:
    """Inyección de dependencia del repositorio de motos."""
    return MotoRepository(db)


def get_moto_service() -> MotoService:
    """Inyección de dependencia del servicio de motos."""
    return MotoService()


# ==================== ENDPOINTS ====================

@router.post(
    "/",
    response_model=ApiResponse[MotoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva moto"
)
async def register_moto(
    request: RegisterMotoRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> ApiResponse[MotoResponse]:
    """
    Registra una nueva moto KTM.
    
    - **vin**: VIN de 17 caracteres (único)
    - **modelo**: Modelo de la moto (ej: Duke 390)
    - **año**: Año de fabricación (1990 - actual + 1)
    - **placa**: Placa de la moto (opcional, único)
    - **color**: Color de la moto (opcional)
    - **kilometraje**: Kilometraje actual (default: 0)
    - **observaciones**: Observaciones adicionales (opcional)
    """
    use_case = RegisterMotoUseCase(repository, service)
    moto = await use_case.execute(request, current_user.id)
    return ApiResponse(
        success=True,
        message="Moto registrada exitosamente",
        data=moto
    )


@router.get(
    "/",
    response_model=PaginatedResponse[MotoResponse],
    summary="Listar motos"
)
async def list_motos(
    filters: Annotated[MotoFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> PaginatedResponse[MotoResponse]:
    """
    Lista motos con filtros y paginación.
    
    - **Usuarios normales**: Solo ven sus propias motos
    - **Admins**: Pueden ver todas las motos y filtrar por usuario
    
    Filtros disponibles:
    - **usuario_id**: ID del usuario (solo admins)
    - **modelo**: Búsqueda parcial por modelo
    - **año_desde/año_hasta**: Rango de años
    - **vin**: Buscar por VIN específico
    - **placa**: Buscar por placa específica
    - **page**: Número de página (default: 1)
    - **per_page**: Items por página (default: 20, max: 100)
    - **order_by**: Campo para ordenar (id, created_at, año, kilometraje, modelo)
    - **order_direction**: Dirección (asc, desc)
    """
    is_admin = current_user.rol == "admin"
    use_case = ListMotosUseCase(repository, service)
    motos, total = await use_case.execute(filters, pagination, current_user.id, is_admin)
    
    # Construir respuestas
    motos_response = [
        MotoResponse(**service.build_moto_response(moto))
        for moto in motos
    ]
    
    return create_paginated_response(
        message="Motos obtenidas exitosamente",
        data=motos_response,
        page=pagination.page,
        per_page=pagination.per_page,
        total_items=total
    )


@router.get(
    "/stats",
    response_model=ApiResponse[MotoStatsResponse],
    summary="Estadísticas de motos (Admin)",
    dependencies=[Depends(require_admin)]
)
async def get_moto_stats(
    repository: Annotated[MotoRepository, Depends(get_moto_repository)]
) -> ApiResponse[MotoStatsResponse]:
    """
    Obtiene estadísticas de motos (solo admins).
    
    Incluye:
    - Total de motos registradas
    - Motos por año de fabricación
    - Kilometraje promedio
    - Modelos más populares (top 10)
    """
    use_case = GetMotoStatsUseCase(repository)
    stats = await use_case.execute()
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=stats
    )


@router.get(
    "/{moto_id}",
    response_model=ApiResponse[MotoResponse],
    summary="Obtener moto por ID"
)
async def get_moto(
    moto_id: int,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> ApiResponse[MotoResponse]:
    """
    Obtiene una moto por ID.
    
    - **Usuarios normales**: Solo pueden ver sus propias motos
    - **Admins**: Pueden ver cualquier moto
    """
    is_admin = current_user.rol == "admin"
    use_case = GetMotoUseCase(repository, service)
    moto = await use_case.execute(moto_id, current_user.id, is_admin)
    return ApiResponse(
        success=True,
        message="Moto obtenida exitosamente",
        data=moto
    )


@router.patch(
    "/{moto_id}",
    response_model=ApiResponse[MotoResponse],
    summary="Actualizar moto"
)
async def update_moto(
    moto_id: int,
    request: UpdateMotoRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> ApiResponse[MotoResponse]:
    """
    Actualiza una moto (actualización parcial).
    
    - **Usuarios normales**: Solo pueden actualizar sus propias motos
    - **Admins**: Pueden actualizar cualquier moto
    
    Campos actualizables:
    - **placa**: Nueva placa (debe ser única)
    - **color**: Nuevo color
    - **kilometraje**: Nuevo kilometraje (debe ser >= actual)
    - **observaciones**: Nuevas observaciones
    """
    is_admin = current_user.rol == "admin"
    use_case = UpdateMotoUseCase(repository, service)
    moto = await use_case.execute(moto_id, request, current_user.id, is_admin)
    return ApiResponse(
        success=True,
        message="Moto actualizada exitosamente",
        data=moto
    )


@router.delete(
    "/{moto_id}",
    response_model=SuccessResponse[None],
    summary="Eliminar moto"
)
async def delete_moto(
    moto_id: int,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> SuccessResponse[None]:
    """
    Elimina una moto (soft delete).
    
    - **Usuarios normales**: Solo pueden eliminar sus propias motos
    - **Admins**: Pueden eliminar cualquier moto
    """
    is_admin = current_user.rol == "admin"
    use_case = DeleteMotoUseCase(repository, service)
    await use_case.execute(moto_id, current_user.id, is_admin)
    return SuccessResponse(
        message="Moto eliminada exitosamente",
        data=None
    )


@router.patch(
    "/{moto_id}/kilometraje",
    response_model=ApiResponse[MotoResponse],
    summary="Actualizar kilometraje"
)
async def update_kilometraje(
    moto_id: int,
    request: UpdateKilometrajeRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    repository: Annotated[MotoRepository, Depends(get_moto_repository)],
    service: Annotated[MotoService, Depends(get_moto_service)]
) -> ApiResponse[MotoResponse]:
    """
    Actualiza solo el kilometraje de una moto.
    
    - **Usuarios normales**: Solo pueden actualizar sus propias motos
    - **Admins**: Pueden actualizar cualquier moto
    
    Validaciones:
    - El nuevo kilometraje debe ser >= al actual
    - El incremento no puede ser mayor a 100,000 km
    """
    is_admin = current_user.rol == "admin"
    use_case = UpdateKilometrajeUseCase(repository, service)
    moto = await use_case.execute(moto_id, request, current_user.id, is_admin)
    return ApiResponse(
        success=True,
        message="Kilometraje actualizado exitosamente",
        data=moto
    )
