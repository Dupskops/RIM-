"""
Rutas REST API para el módulo de fallas (MVP v2.3).

Endpoints:
- POST /fallas - Crear nueva falla
- GET /fallas/{id} - Obtener falla por ID
- GET /fallas/codigo/{codigo} - Obtener falla por código
- GET /motos/{moto_id}/fallas - Listar fallas de una moto
- PATCH /fallas/{id} - Actualizar campos editables
- POST /fallas/{id}/diagnosticar - Mover a EN_REPARACION
- POST /fallas/{id}/resolver - Mover a RESUELTA
- GET /motos/{moto_id}/fallas/stats - Estadísticas (Premium)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_db, get_current_user
from src.shared.base_models import PaginationParams
from src.shared.exceptions import ResourceNotFoundException, ValidationException
from ..auth.models import Usuario

from .use_cases import (
    CreateFallaUseCase,
    GetFallaByIdUseCase,
    GetFallaByCodigoUseCase,
    ListFallasByMotoUseCase,
    UpdateFallaUseCase,
    DiagnosticarFallaUseCase,
    ResolverFallaUseCase,
    GetFallaStatsUseCase
)
from .schemas import (
    FallaCreate,
    FallaUpdate,
    FallaResponse,
    FallaListResponse,
    FallaStatsResponse,
    FallaFilterParams
)

router = APIRouter(prefix="/fallas", tags=["Fallas"])


# =============================================================================
# CREAR FALLA
# =============================================================================

@router.post(
    "",
    response_model=FallaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva falla",
    description="Crea una nueva falla (detección automática o reporte manual)"
)
async def create_falla(
    data: FallaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear una nueva falla.
    
    - **moto_id**: ID de la moto
    - **componente_id**: ID del componente afectado
    - **tipo**: Tipo de falla (string libre, ej: "sobrecalentamiento")
    - **descripcion**: Descripción detallada (opcional)
    - **severidad**: baja, media, alta, critica
    - **origen_deteccion**: sensor, ml, manual
    
    Genera automáticamente:
    - Código único (FL-YYYYMMDD-NNN)
    - puede_conducir (según tipo y severidad)
    - requiere_atencion_inmediata
    - solucion_sugerida
    """
    try:
        use_case = CreateFallaUseCase(db)
        falla = await use_case.execute(data, usuario_id=current_user.id)
        return falla
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# OBTENER FALLA POR ID
# =============================================================================

@router.get(
    "/{falla_id}",
    response_model=FallaResponse,
    summary="Obtener falla por ID"
)
async def get_falla(
    falla_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene una falla por su ID."""
    try:
        use_case = GetFallaByIdUseCase(db)
        falla = await use_case.execute(falla_id)
        return falla
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# OBTENER FALLA POR CÓDIGO
# =============================================================================

@router.get(
    "/codigo/{codigo}",
    response_model=FallaResponse,
    summary="Obtener falla por código"
)
async def get_falla_by_codigo(
    codigo: str,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una falla por su código único.
    
    Ejemplo: FL-20251110-001
    """
    try:
        use_case = GetFallaByCodigoUseCase(db)
        falla = await use_case.execute(codigo)
        return falla
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# LISTAR FALLAS DE UNA MOTO
# =============================================================================

@router.get(
    "/motos/{moto_id}",
    response_model=dict,
    summary="Listar fallas de una moto"
)
async def list_fallas(
    moto_id: int,
    solo_activas: bool = Query(False, description="Solo fallas no resueltas"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: int = Query(50, ge=1, le=100, description="Límite"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista las fallas de una moto con paginación.
    
    - **solo_activas**: Si es true, solo devuelve fallas no resueltas
    - **skip/limit**: Para paginación
    """
    try:
        filters = FallaFilterParams(moto_id=moto_id, solo_activas=solo_activas)
        pagination = PaginationParams(offset=skip, limit=limit)
        
        use_case = ListFallasByMotoUseCase(db)
        fallas, total = await use_case.execute(filters, pagination)
        
        return {
            "items": [FallaListResponse.model_validate(f) for f in fallas],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# ACTUALIZAR FALLA
# =============================================================================

@router.patch(
    "/{falla_id}",
    response_model=FallaResponse,
    summary="Actualizar falla"
)
async def update_falla(
    falla_id: int,
    data: FallaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza campos editables de una falla.
    
    Campos permitidos:
    - descripcion
    - severidad
    - solucion_sugerida
    - latitud/longitud
    
    Para cambiar el estado, usar endpoints específicos:
    - POST /fallas/{id}/diagnosticar (DETECTADA -> EN_REPARACION)
    - POST /fallas/{id}/resolver (EN_REPARACION -> RESUELTA)
    """
    try:
        use_case = UpdateFallaUseCase(db)
        falla = await use_case.execute(falla_id, data, usuario_id=current_user.id)
        return falla
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# DIAGNOSTICAR FALLA (DETECTADA -> EN_REPARACION)
# =============================================================================

@router.post(
    "/{falla_id}/diagnosticar",
    response_model=FallaResponse,
    summary="Diagnosticar falla (mover a EN_REPARACION)"
)
async def diagnosticar_falla(
    falla_id: int,
    solucion_sugerida: str = Query(..., min_length=10, description="Solución propuesta"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Diagnostica una falla y la mueve a estado EN_REPARACION.
    
    - Valida transición: DETECTADA -> EN_REPARACION
    - Actualiza solucion_sugerida
    - Emite evento FallaActualizada
    
    En v2.3, los datos de diagnóstico (costo estimado, notas técnico)
    se manejan en la tabla `mantenimientos`.
    """
    try:
        use_case = DiagnosticarFallaUseCase(db)
        falla = await use_case.execute(falla_id, solucion_sugerida, usuario_id=current_user.id)
        return falla
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# RESOLVER FALLA (EN_REPARACION -> RESUELTA)
# =============================================================================

@router.post(
    "/{falla_id}/resolver",
    response_model=FallaResponse,
    summary="Resolver falla (mover a RESUELTA)"
)
async def resolver_falla(
    falla_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Resuelve una falla marcándola como RESUELTA.
    
    - Valida transición: EN_REPARACION -> RESUELTA
    - Registra fecha_resolucion
    - Calcula días de resolución
    - Emite evento FallaResuelta
    
    En v2.3, los datos de resolución (solución aplicada, costo real)
    se manejan en la tabla `mantenimientos`.
    """
    try:
        use_case = ResolverFallaUseCase(db)
        falla = await use_case.execute(falla_id, usuario_id=current_user.id)
        return falla
    except ResourceNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# ESTADÍSTICAS (PREMIUM)
# =============================================================================

@router.get(
    "/motos/{moto_id}/stats",
    response_model=FallaStatsResponse,
    summary="Estadísticas de fallas (Premium)",
    description="Obtiene estadísticas agregadas de fallas de una moto. Requiere plan Pro."
)
async def get_falla_stats(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas de fallas de una moto.
    
    Incluye:
    - Total de fallas (activas, resueltas, críticas)
    - Distribución por tipo, severidad, estado
    - Tiempo promedio de resolución
    
    **Requiere plan Premium**
    """
    # TODO: Validar que el usuario tiene plan Pro
    # if not current_user.es_premium:
    #     raise HTTPException(status_code=403, detail="Requiere plan Premium")
    
    try:
        use_case = GetFallaStatsUseCase(db)
        stats = await use_case.execute(moto_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
