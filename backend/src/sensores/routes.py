"""
Rutas API para sensores IoT.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.dependencies import get_db, get_current_user
from ..auth.models import Usuario
from ..shared.middleware import FeatureChecker
from ..shared.constants import Feature
from src.shared.base_models import (
    ApiResponse,
)
from .repositories import SensorRepository, LecturaSensorRepository
from .services import SensorService
from .schemas import (
    CreateSensorRequest,
    CreateLecturaRequest,
    SensorResponse,
    LecturaSensorResponse,
    SensorStatsResponse
)
from .use_cases import (
    CreateSensorUseCase,
    RegisterLecturaUseCase,
    GetSensorStatsUseCase
)


router = APIRouter()


# ==================== DEPENDENCIES ====================

async def get_sensor_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> SensorRepository:
    """Inyección de dependencia del repositorio de sensores."""
    return SensorRepository(db)


async def get_lectura_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> LecturaSensorRepository:
    """Inyección de dependencia del repositorio de lecturas."""
    return LecturaSensorRepository(db)


def get_sensor_service() -> SensorService:
    """Inyección de dependencia del servicio de sensores."""
    return SensorService()


# ==================== ENDPOINTS ====================

@router.post(
    "/",
    response_model=ApiResponse[SensorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sensor"
)
async def create_sensor(
    request: CreateSensorRequest,
    sensor_repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    service: Annotated[SensorService, Depends(get_sensor_service)],
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Registra un nuevo sensor IoT en una moto.
    
    - **moto_id**: ID de la moto
    - **tipo**: Tipo de sensor (temperatura_motor, presion_aceite, etc.)
    - **codigo**: Código único del sensor
    - **frecuencia_lectura**: Frecuencia de lectura en segundos
    - **umbral_min/max**: Umbrales para alertas
    """
    use_case = CreateSensorUseCase(sensor_repo, service)
    sensor = await use_case.execute(request)
    return ApiResponse(
        success=True,
        message="Sensor registrado exitosamente",
        data=sensor
    )


@router.post(
    "/lecturas",
    response_model=ApiResponse[LecturaSensorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar lectura"
)
async def register_lectura(
    request: CreateLecturaRequest,
    sensor_repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    lectura_repo: Annotated[LecturaSensorRepository, Depends(get_lectura_repository)],
    service: Annotated[SensorService, Depends(get_sensor_service)]
):
    """
    Registra una lectura de sensor IoT.
    
    - **sensor_id**: ID del sensor
    - **valor**: Valor leído
    - **timestamp_lectura**: Timestamp de la lectura del dispositivo
    - **metadata_json**: Metadata adicional (opcional)
    """
    use_case = RegisterLecturaUseCase(sensor_repo, lectura_repo, service)
    lectura = await use_case.execute(request)
    return ApiResponse(
        success=True,
        message="Lectura registrada exitosamente",
        data=lectura
    )


@router.get(
    "/stats",
    response_model=ApiResponse[SensorStatsResponse],
    summary="Estadísticas de sensores (Premium)"
)
async def get_stats(
    sensor_repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    lectura_repo: Annotated[LecturaSensorRepository, Depends(get_lectura_repository)],
    current_user: Annotated[Usuario, Depends(get_current_user)],
    _: bool = Depends(FeatureChecker(Feature.REPORTES_AVANZADOS)),
    moto_id: int | None = None
):
    """
    Obtiene estadísticas avanzadas de sensores y lecturas.
    
    **Requiere plan Premium** (feature: REPORTES_AVANZADOS)
    
    - **moto_id**: Filtrar por moto (opcional)
    """
    use_case = GetSensorStatsUseCase(sensor_repo, lectura_repo)
    stats = await use_case.execute(moto_id)
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=stats
    )
