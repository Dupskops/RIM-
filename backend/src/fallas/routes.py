"""
Rutas REST API para el módulo de fallas.
Endpoints para gestión de fallas detectadas en motos.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    FallaCreate,
    FallaMLCreate,
    FallaUpdate,
    FallaDiagnosticar,
    FallaResolver,
    FallaResponse,
    FallaStatsResponse,
    FallaFilterParams
)
from .use_cases import (
    CreateFallaUseCase,
    CreateFallaMLUseCase,
    UpdateFallaUseCase,
    DiagnosticarFallaUseCase,
    ResolverFallaUseCase,
    GetFallaUseCase,
    ListFallasByMotoUseCase,
    GetFallaStatsUseCase,
    DeleteFallaUseCase
)
from ..config.database import get_db
from ..shared.middleware import FeatureChecker
from ..shared.constants import Feature
from ..shared.base_models import (
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    PaginationParams,
    create_success_response,
    create_paginated_response
)


router = APIRouter()


@router.post(
    "/",
    response_model=ApiResponse[FallaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva falla",
    description="Registra una nueva falla detectada en una moto"
)
async def create_falla(
    data: FallaCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Crea una nueva falla.
    
    - **moto_id**: ID de la moto
    - **tipo**: Tipo de falla (sobrecalentamiento, bateria_baja, etc.)
    - **titulo**: Título descriptivo
    - **descripcion**: Descripción detallada
    - **severidad**: baja, media, alta, critica
    """
    use_case = CreateFallaUseCase(db)
    falla = await use_case.execute(data)
    return create_success_response(
        message="Falla creada exitosamente",
        data=falla
    )


@router.post(
    "/ml",
    response_model=ApiResponse[FallaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear falla detectada por ML/IA",
    description="Registra una falla detectada automáticamente por modelos de Machine Learning"
)
async def create_falla_ml(
    data: FallaMLCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Crea una falla detectada por ML.
    
    Incluye información adicional como:
    - **confianza_ml**: Nivel de confianza del modelo (0-1)
    - **modelo_ml_usado**: Nombre del modelo
    - **prediccion_ml**: Detalles de la predicción en JSON
    """
    use_case = CreateFallaMLUseCase(db)
    falla = await use_case.execute(data)
    return create_success_response(
        message="Falla detectada por IA creada exitosamente",
        data=falla
    )


@router.get(
    "/{falla_id}",
    response_model=ApiResponse[FallaResponse],
    summary="Obtener falla por ID",
    description="Obtiene información detallada de una falla específica"
)
async def get_falla(
    falla_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Obtiene una falla por su ID.
    
    Retorna toda la información incluyendo:
    - Datos de detección
    - Diagnóstico (si existe)
    - Resolución (si está resuelta)
    - Costos estimados y reales
    """
    use_case = GetFallaUseCase(db)
    falla = await use_case.execute(falla_id)
    return create_success_response(
        message="Falla obtenida exitosamente",
        data=falla
    )


@router.get(
    "/moto/{moto_id}",
    response_model=PaginatedResponse[FallaResponse],
    summary="Listar fallas de una moto",
    description="Obtiene todas las fallas de una moto específica"
)
async def list_fallas_by_moto(
    moto_id: int,
    filters: Annotated[FallaFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[FallaResponse]:
    """
    Lista fallas de una moto.
    
    Parámetros de filtro:
    - **solo_activas**: true para solo fallas sin resolver
    - **skip**: Paginación - registros a saltar
    - **limit**: Paginación - máximo de registros
    """
    # Forzar moto_id del path
    filters.moto_id = moto_id
    
    use_case = ListFallasByMotoUseCase(db)
    fallas, total = await use_case.execute(filters, pagination)
    
    return create_paginated_response(
        message="Fallas obtenidas exitosamente",
        data=fallas,
        page=pagination.page,
        per_page=pagination.per_page,
        total_items=total
    )


@router.patch(
    "/{falla_id}",
    response_model=ApiResponse[FallaResponse],
    summary="Actualizar falla",
    description="Actualiza información de una falla existente"
)
async def update_falla(
    falla_id: int,
    data: FallaUpdate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Actualiza una falla.
    
    Permite actualizar:
    - Estado
    - Severidad
    - Solución aplicada
    - Costo real
    - Notas del técnico
    """
    use_case = UpdateFallaUseCase(db)
    falla = await use_case.execute(falla_id, data)
    return create_success_response(
        message="Falla actualizada exitosamente",
        data=falla
    )


@router.post(
    "/{falla_id}/diagnosticar",
    response_model=ApiResponse[FallaResponse],
    summary="Diagnosticar falla",
    description="Marca una falla como diagnosticada con solución propuesta"
)
async def diagnosticar_falla(
    falla_id: int,
    data: FallaDiagnosticar,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Diagnostica una falla.
    
    Establece:
    - Solución sugerida
    - Costo estimado
    - Notas del técnico
    - Cambia estado a "en_revision"
    """
    use_case = DiagnosticarFallaUseCase(db)
    falla = await use_case.execute(falla_id, data)
    return create_success_response(
        message="Falla diagnosticada exitosamente",
        data=falla
    )


@router.post(
    "/{falla_id}/resolver",
    response_model=ApiResponse[FallaResponse],
    summary="Resolver falla",
    description="Marca una falla como resuelta"
)
async def resolver_falla(
    falla_id: int,
    data: FallaResolver,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[FallaResponse]:
    """
    Resuelve una falla.
    
    Registra:
    - Solución aplicada
    - Costo real
    - Notas finales
    - Fecha de resolución
    - Cambia estado a "resuelta"
    """
    use_case = ResolverFallaUseCase(db)
    falla = await use_case.execute(falla_id, data)
    return create_success_response(
        message="Falla resuelta exitosamente",
        data=falla
    )


@router.get(
    "/moto/{moto_id}/stats",
    response_model=ApiResponse[FallaStatsResponse],
    summary="Estadísticas de fallas (Premium)",
    description="Obtiene estadísticas completas de fallas de una moto"
)
async def get_falla_stats(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    feature_check: None = Depends(FeatureChecker(Feature.REPORTES_AVANZADOS))
) -> ApiResponse[FallaStatsResponse]:
    """
    Obtiene estadísticas de fallas (requiere Premium).
    
    Incluye:
    - Total de fallas, activas, resueltas, críticas
    - Distribución por tipo, severidad y estado
    - Tiempo promedio de resolución
    - Costo total de reparaciones
    - Tasa de resolución
    
    **⭐ Feature Premium**: Requiere suscripción Premium para acceder.
    """
    use_case = GetFallaStatsUseCase(db)
    stats = await use_case.execute(moto_id)
    return create_success_response(
        message="Estadísticas de fallas obtenidas exitosamente",
        data=stats
    )


@router.delete(
    "/{falla_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Eliminar falla",
    description="Elimina (soft delete) una falla"
)
async def delete_falla(
    falla_id: int,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """
    Elimina una falla.
    
    Nota: Es un soft delete, no se elimina físicamente de la BD.
    No se pueden eliminar fallas:
    - En estado "en_revision"
    - Críticas sin resolver
    """
    use_case = DeleteFallaUseCase(db)
    await use_case.execute(falla_id)
    return create_success_response(
        message="Falla eliminada exitosamente",
        data=None
    )
