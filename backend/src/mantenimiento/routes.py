"""
Rutas API para el módulo de mantenimiento.
"""
from typing import List, Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_db
from src.shared.middleware import FeatureChecker
from src.shared.constants import Feature
from src.shared.base_models import (
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    PaginationParams,
    create_success_response,
    create_paginated_response
)
from src.mantenimiento.repositories import MantenimientoRepository
from src.mantenimiento.schemas import (
    MantenimientoCreate,
    MantenimientoMLCreate,
    MantenimientoUpdate,
    MantenimientoIniciar,
    MantenimientoCompletar,
    MantenimientoResponse,
    MantenimientoFilterParams,
    MantenimientoStatsResponse
)
from src.mantenimiento.use_cases import (
    CreateMantenimientoUseCase,
    CreateMantenimientoMLUseCase,
    UpdateMantenimientoUseCase,
    IniciarMantenimientoUseCase,
    CompletarMantenimientoUseCase,
    GetMantenimientoUseCase,
    ListMantenimientosByMotoUseCase,
    GetMantenimientoStatsUseCase,
    DeleteMantenimientoUseCase
)

router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[MantenimientoResponse],
    status_code=201,
    summary="Crear mantenimiento",
    description="Crea un nuevo mantenimiento programado para una motocicleta"
)
async def create_mantenimiento(
    data: MantenimientoCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Crea un nuevo mantenimiento."""
    repository = MantenimientoRepository(db)
    use_case = CreateMantenimientoUseCase(repository)
    mantenimiento = await use_case.execute(data)
    return create_success_response(
        message="Mantenimiento creado exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.post(
    "/ml",
    response_model=ApiResponse[MantenimientoResponse],
    status_code=201,
    summary="Crear mantenimiento por IA",
    description="Crea un mantenimiento recomendado por el sistema de IA",
    dependencies=[Depends(FeatureChecker(Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA))]
)
async def create_mantenimiento_ml(
    data: MantenimientoMLCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Crea un mantenimiento recomendado por IA (Premium)."""
    repository = MantenimientoRepository(db)
    use_case = CreateMantenimientoMLUseCase(repository)
    mantenimiento = await use_case.execute(data)
    return create_success_response(
        message="Mantenimiento recomendado por IA creado exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.get(
    "/{mantenimiento_id}",
    response_model=ApiResponse[MantenimientoResponse],
    summary="Obtener mantenimiento",
    description="Obtiene los detalles de un mantenimiento específico"
)
async def get_mantenimiento(
    mantenimiento_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Obtiene un mantenimiento por ID."""
    repository = MantenimientoRepository(db)
    use_case = GetMantenimientoUseCase(repository)
    mantenimiento = await use_case.execute(mantenimiento_id)
    return create_success_response(
        message="Mantenimiento obtenido exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.get(
    "/moto/{moto_id}",
    response_model=PaginatedResponse[MantenimientoResponse],
    summary="Listar mantenimientos de moto",
    description="Lista todos los mantenimientos de una motocicleta específica"
)
async def list_mantenimientos_by_moto(
    moto_id: int,
    filters: Annotated[MantenimientoFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[MantenimientoResponse]:
    """Lista mantenimientos de una moto."""
    # Forzar filtro por moto_id
    filters.moto_id = moto_id
    
    repository = MantenimientoRepository(db)
    use_case = ListMantenimientosByMotoUseCase(repository)
    mantenimientos, total = await use_case.execute(filters, pagination)
    
    mantenimientos_response = [
        MantenimientoResponse.model_validate(m) for m in mantenimientos
    ]
    
    return create_paginated_response(
        message="Mantenimientos obtenidos exitosamente",
        data=mantenimientos_response,
        page=pagination.page,
        per_page=pagination.limit,
        total_items=total
    )


@router.patch(
    "/{mantenimiento_id}",
    response_model=ApiResponse[MantenimientoResponse],
    summary="Actualizar mantenimiento",
    description="Actualiza la información de un mantenimiento"
)
async def update_mantenimiento(
    mantenimiento_id: int,
    data: MantenimientoUpdate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Actualiza un mantenimiento."""
    repository = MantenimientoRepository(db)
    use_case = UpdateMantenimientoUseCase(repository)
    mantenimiento = await use_case.execute(mantenimiento_id, data)
    return create_success_response(
        message="Mantenimiento actualizado exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.post(
    "/{mantenimiento_id}/iniciar",
    response_model=ApiResponse[MantenimientoResponse],
    summary="Iniciar mantenimiento",
    description="Marca un mantenimiento como iniciado y registra el mecánico y taller"
)
async def iniciar_mantenimiento(
    mantenimiento_id: int,
    data: MantenimientoIniciar,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Inicia un mantenimiento."""
    repository = MantenimientoRepository(db)
    use_case = IniciarMantenimientoUseCase(repository)
    mantenimiento = await use_case.execute(mantenimiento_id, data)
    return create_success_response(
        message="Mantenimiento iniciado exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.post(
    "/{mantenimiento_id}/completar",
    response_model=ApiResponse[MantenimientoResponse],
    summary="Completar mantenimiento",
    description="Marca un mantenimiento como completado con costos y detalles finales"
)
async def completar_mantenimiento(
    mantenimiento_id: int,
    data: MantenimientoCompletar,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoResponse]:
    """Completa un mantenimiento."""
    repository = MantenimientoRepository(db)
    use_case = CompletarMantenimientoUseCase(repository)
    mantenimiento = await use_case.execute(mantenimiento_id, data)
    return create_success_response(
        message="Mantenimiento completado exitosamente",
        data=MantenimientoResponse.model_validate(mantenimiento)
    )


@router.get(
    "/moto/{moto_id}/stats",
    response_model=ApiResponse[MantenimientoStatsResponse],
    summary="Estadísticas de mantenimiento (Premium)",
    description="Obtiene estadísticas detalladas de mantenimientos de una moto",
    dependencies=[Depends(FeatureChecker(Feature.REPORTES_AVANZADOS))]
)
async def get_mantenimiento_stats(
    moto_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[MantenimientoStatsResponse]:
    """Obtiene estadísticas de mantenimientos (Premium)."""
    repository = MantenimientoRepository(db)
    use_case = GetMantenimientoStatsUseCase(repository)
    stats = await use_case.execute(moto_id=moto_id)
    return create_success_response(
        message="Estadísticas de mantenimiento obtenidas exitosamente",
        data=stats
    )


@router.delete(
    "/{mantenimiento_id}",
    response_model=SuccessResponse[None],
    status_code=200,
    summary="Eliminar mantenimiento",
    description="Elimina un mantenimiento (solo si está pendiente o cancelado)"
)
async def delete_mantenimiento(
    mantenimiento_id: int,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Elimina un mantenimiento (soft delete)."""
    repository = MantenimientoRepository(db)
    use_case = DeleteMantenimientoUseCase(repository)
    await use_case.execute(mantenimiento_id)
    return create_success_response(
        message="Mantenimiento eliminado exitosamente",
        data=None
    )
