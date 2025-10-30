from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.dependencies import get_db, get_current_user
from src.shared.base_models import ApiResponse
from .schemas import MotoCreateSchema, MotoReadSchema, MotoUpdateSchema, EstadoActualSchema, DiagnosticoGeneralSchema
from .use_cases import (
    CreateMotoUseCase,
    GetMotoUseCase,
    ListMotosUseCase,
    UpdateMotoUseCase,
    DeleteMotoUseCase,
    GetEstadoActualUseCase,
    GetDiagnosticoGeneralUseCase
)


router = APIRouter()


@router.post("", response_model=ApiResponse[MotoReadSchema], status_code=status.HTTP_201_CREATED)
async def create_moto(
    data: MotoCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = CreateMotoUseCase(db)
    moto = await use_case.execute(data, current_user["id"])
    return ApiResponse.success(data=moto, message="Moto creada exitosamente")


@router.get("/{moto_id}", response_model=ApiResponse[MotoReadSchema])
async def get_moto(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = GetMotoUseCase(db)
    moto = await use_case.execute(moto_id, current_user["id"])
    return ApiResponse.success(data=moto)


@router.get("", response_model=ApiResponse[List[MotoReadSchema]])
async def list_motos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = ListMotosUseCase(db)
    motos = await use_case.execute(current_user["id"], skip, limit)
    return ApiResponse.success(data=motos)


@router.patch("/{moto_id}", response_model=ApiResponse[MotoReadSchema])
async def update_moto(
    moto_id: int,
    data: MotoUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = UpdateMotoUseCase(db)
    moto = await use_case.execute(moto_id, data, current_user["id"])
    return ApiResponse.success(data=moto, message="Moto actualizada exitosamente")


@router.delete("/{moto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moto(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = DeleteMotoUseCase(db)
    await use_case.execute(moto_id, current_user["id"])


@router.get("/{moto_id}/estado-actual", response_model=ApiResponse[List[EstadoActualSchema]])
async def get_estado_actual(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = GetEstadoActualUseCase(db)
    estados = await use_case.execute(moto_id, current_user["id"])
    return ApiResponse.success(data=estados)


@router.get("/{moto_id}/diagnostico", response_model=ApiResponse[DiagnosticoGeneralSchema])
async def get_diagnostico_general(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    use_case = GetDiagnosticoGeneralUseCase(db)
    diagnostico = await use_case.execute(moto_id, current_user["id"])
    return ApiResponse.success(data=diagnostico)
