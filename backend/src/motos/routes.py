from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.dependencies import get_db, get_current_user_id
from src.shared.base_models import ApiResponse, create_success_response
from .schemas import (
    MotoCreateSchema, MotoReadSchema, MotoUpdateSchema, 
    EstadoActualSchema, DiagnosticoGeneralSchema, ModeloMotoSchema
)
from .use_cases import (
    CreateMotoUseCase,
    GetMotoUseCase,
    ListMotosUseCase,
    UpdateMotoUseCase,
    DeleteMotoUseCase,
    GetEstadoActualUseCase,
    GetDiagnosticoGeneralUseCase,
    ListModelosDisponiblesUseCase
)


router = APIRouter()


# Prefer using get_current_user_id dependency which extracts user id from the Authorization header token


# ============================================
# ENDPOINTS DE MODELOS (CATÁLOGO)
# ============================================

@router.get("/modelos-disponibles", response_model=ApiResponse[List[ModeloMotoSchema]])
async def list_modelos_disponibles(
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos los modelos de moto disponibles (activos).
    
    Este endpoint es usado en el flujo de onboarding cuando el usuario
    registra su primera moto. Puede ser público o requerir autenticación mínima.
    """
    use_case = ListModelosDisponiblesUseCase(db)
    modelos = await use_case.execute()
    return create_success_response("", modelos)


# ============================================
# ENDPOINTS DE MOTOS (CRUD)
# ============================================

@router.post("", response_model=ApiResponse[MotoReadSchema], status_code=status.HTTP_201_CREATED)
async def create_moto(
    data: MotoCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    use_case = CreateMotoUseCase(db)
    moto = await use_case.execute(data, user_id)
    return create_success_response("Moto creada exitosamente", moto)


@router.get("/{moto_id}", response_model=ApiResponse[MotoReadSchema])
async def get_moto(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    use_case = GetMotoUseCase(db)
    moto = await use_case.execute(moto_id, user_id)
    return create_success_response("", moto)


@router.get("", response_model=ApiResponse[List[MotoReadSchema]])
async def list_motos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    use_case = ListMotosUseCase(db)
    motos = await use_case.execute(user_id, skip, limit)
    return create_success_response("", motos)


@router.patch("/{moto_id}", response_model=ApiResponse[MotoReadSchema])
async def update_moto(
    moto_id: int,
    data: MotoUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    use_case = UpdateMotoUseCase(db)
    moto = await use_case.execute(moto_id, data, user_id)
    return create_success_response("Moto actualizada exitosamente", moto)


@router.delete("/{moto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moto(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Elimina una moto del usuario.
    
    CASCADA: Al eliminar la moto se eliminan automáticamente:
    - estado_actual (11 registros)
    - lecturas (todas las telemetrías)
    - sensores (virtuales del gemelo digital)
    - fallas relacionadas
    - mantenimientos relacionados
    - viajes relacionados
    """
    use_case = DeleteMotoUseCase(db)
    await use_case.execute(moto_id, user_id)


# ============================================
# ENDPOINTS DE ESTADO Y DIAGNÓSTICO
# ============================================

@router.get("/{moto_id}/estado-actual", response_model=ApiResponse[List[EstadoActualSchema]])
async def get_estado_actual(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene el estado actual de todos los componentes de la moto (11 total).
    
    Este endpoint es usado por el dashboard para mostrar el estado en tiempo real.
    Incluye: Motor, Frenos, Neumáticos, Batería, etc.
    
    Returns:
        Lista de 11 estados (uno por componente) con: componente, estado, último_valor
    """
    use_case = GetEstadoActualUseCase(db)
    estados = await use_case.execute(moto_id, user_id)
    return create_success_response("", estados)


@router.get("/{moto_id}/diagnostico", response_model=ApiResponse[DiagnosticoGeneralSchema])
async def get_diagnostico_general(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene el diagnóstico general de la moto.
    
    Calcula el estado general basado en el peor estado de todos los componentes.
    Incluye: estado_general (EXCELENTE/BUENO/ATENCION/CRITICO) + desglose por componente.
    
    Returns:
        Diagnóstico con estado general calculado
    """
    use_case = GetDiagnosticoGeneralUseCase(db)
    diagnostico = await use_case.execute(moto_id, user_id)
    return create_success_response("", diagnostico)
