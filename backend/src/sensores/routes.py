"""
Rutas REST API para el módulo de sensores.

Endpoints:
- Templates: CRUD de plantillas (admin)
- Sensors: CRUD de sensores
- Lecturas: Registrar y consultar telemetría
- Provisión: Auto-provisión de sensores para una moto
- Stats: Estadísticas agregadas

Incluye:
- Validación de permisos
- Manejo de errores
- Logging
- Respuestas estandarizadas
"""
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..config.dependencies import get_current_user, require_admin
from ..usuarios.models import Usuario
from ..shared.base_models import ApiResponse
from ..shared.exceptions import NotFoundError, ValidationError

from .schemas import (
    SensorTemplateCreate, SensorTemplateRead,
    CreateSensorRequest, UpdateSensorRequest, SensorRead,
    CreateLecturaRequest, LecturaRead,
    SensorStatsResponse, ComponentStateResponse
)
from .use_cases import (
    CreateSensorTemplateUseCase,
    GetSensorTemplateUseCase,
    CreateSensorUseCase,
    UpdateSensorUseCase,
    CreateLecturaUseCase,
    ProvisionSensorsUseCase,
    UpdateComponentStateUseCase,
    GetSensorStatsUseCase
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensores", tags=["Sensores"])


# ==================== SENSOR TEMPLATES (ADMIN) ====================

@router.post(
    "/templates",
    response_model=ApiResponse[SensorTemplateRead],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)]
)
async def create_sensor_template(
    data: SensorTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear plantilla de sensor (solo admin).
    
    Plantillas definen configuraciones predefinidas de sensores
    que se pueden instanciar para motos específicas.
    """
    try:
        logger.info(f"Admin {current_user.id} creando template: modelo={data.modelo}")
        
        use_case = CreateSensorTemplateUseCase(db)
        template = await use_case.execute(data)
        
        return ApiResponse(
            success=True,
            message="Template creado exitosamente",
            data=template
        )
        
    except ValidationError as e:
        logger.warning(f"Validación fallida: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear template"
        )


@router.get(
    "/templates/{template_id}",
    response_model=ApiResponse[SensorTemplateRead]
)
async def get_sensor_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener plantilla de sensor por ID."""
    try:
        use_case = GetSensorTemplateUseCase(db)
        template = await use_case.execute(template_id)
        
        return ApiResponse(
            success=True,
            message="Template obtenido exitosamente",
            data=template
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


# ==================== SENSORS ====================

@router.post(
    "/sensors",
    response_model=ApiResponse[SensorRead],
    status_code=status.HTTP_201_CREATED
)
async def create_sensor(
    data: CreateSensorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear sensor para una moto.
    
    El usuario debe ser propietario de la moto.
    """
    try:
        logger.info(
            f"Usuario {current_user.id} creando sensor: "
            f"moto_id={data.moto_id}, tipo={data.tipo}"
        )
        
        # TODO: Validar que current_user sea propietario de la moto
        
        use_case = CreateSensorUseCase(db)
        sensor = await use_case.execute(data)
        
        return ApiResponse(
            success=True,
            message="Sensor creado exitosamente",
            data=sensor
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando sensor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


@router.get(
    "/sensors/{sensor_id}",
    response_model=ApiResponse[SensorRead]
)
async def get_sensor(
    sensor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener sensor por ID."""
    try:
        from .repositories import SensorRepository
        from .validators import validate_sensor_exists
        
        sensor = await validate_sensor_exists(db, sensor_id)
        
        # TODO: Validar que current_user sea propietario de la moto del sensor
        
        return ApiResponse(
            success=True,
            message="Sensor obtenido exitosamente",
            data=SensorRead.model_validate(sensor)
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo sensor {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


@router.put(
    "/sensors/{sensor_id}",
    response_model=ApiResponse[SensorRead]
)
async def update_sensor(
    sensor_id: UUID,
    data: UpdateSensorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar configuración de sensor."""
    try:
        # TODO: Validar ownership
        
        use_case = UpdateSensorUseCase(db)
        sensor = await use_case.execute(sensor_id, data)
        
        return ApiResponse(
            success=True,
            message="Sensor actualizado exitosamente",
            data=sensor
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error actualizando sensor {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


@router.get(
    "/motos/{moto_id}/sensors",
    response_model=ApiResponse[List[SensorRead]]
)
async def list_sensors_by_moto(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todos los sensores de una moto."""
    try:
        from .repositories import SensorRepository
        from .validators import validate_moto_exists
        
        # Validar moto existe
        await validate_moto_exists(db, moto_id)
        
        # TODO: Validar ownership
        
        # Obtener sensores
        repo = SensorRepository(db)
        sensores = await repo.get_by_moto(moto_id)
        
        return ApiResponse(
            success=True,
            message="Sensores obtenidos exitosamente",
            data=[SensorRead.model_validate(s) for s in sensores]
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error listando sensores de moto {moto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


# ==================== LECTURAS ====================

@router.post(
    "/lecturas",
    response_model=ApiResponse[LecturaRead],
    status_code=status.HTTP_201_CREATED
)
async def create_lectura(
    data: CreateLecturaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registrar lectura de sensor.
    
    Flujo completo:
    - Validar sensor existe
    - Persistir lectura
    - Actualizar last_seen del sensor
    - Verificar umbrales y emitir alertas
    - Emitir eventos
    """
    try:
        logger.info(f"Registrando lectura: sensor_id={data.sensor_id}")
        
        # TODO: Validar ownership
        
        use_case = CreateLecturaUseCase(db)
        lectura = await use_case.execute(data)
        
        await db.commit()  # Commit explícito
        
        return ApiResponse(
            success=True,
            message="Lectura registrada exitosamente",
            data=lectura
        )
        
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error registrando lectura: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


@router.get(
    "/sensors/{sensor_id}/lecturas",
    response_model=ApiResponse[List[LecturaRead]]
)
async def list_lecturas_by_sensor(
    sensor_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar lecturas de un sensor."""
    try:
        from .repositories import LecturaRepository
        from .validators import validate_sensor_exists
        
        # Validar sensor existe
        await validate_sensor_exists(db, sensor_id)
        
        # TODO: Validar ownership
        
        # Obtener lecturas
        repo = LecturaRepository(db)
        lecturas = await repo.list_by_sensor(sensor_id, skip=skip, limit=limit)
        
        return ApiResponse(
            success=True,
            message="Lecturas obtenidas exitosamente",
            data=[LecturaRead.model_validate(l) for l in lecturas]
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error listando lecturas de sensor {sensor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


# ==================== PROVISIÓN ====================

@router.post(
    "/provision/{moto_id}",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED
)
async def provision_sensors(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Auto-provisionar sensores para una moto basados en su modelo.
    
    Lee templates, crea componentes y sensores automáticamente.
    """
    try:
        logger.info(f"Usuario {current_user.id} provisionando sensores: moto_id={moto_id}")
        
        # TODO: Validar ownership
        
        use_case = ProvisionSensorsUseCase(db)
        result = await use_case.execute(moto_id)
        
        await db.commit()
        
        return ApiResponse(
            success=True,
            message=(
                f"Provisión completada: {result['componentes_creados']} componentes, "
                f"{result['sensores_creados']} sensores creados"
            ),
            data=result
        )
        
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error provisionando sensores para moto {moto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


# ==================== COMPONENT STATE ====================

@router.post(
    "/componentes/{componente_id}/update-state",
    response_model=ApiResponse[ComponentStateResponse]
)
async def update_component_state(
    componente_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar estado agregado de un componente basado en sus sensores.
    
    Calcula el component_state a partir de los sensor_state de sus sensores.
    """
    try:
        # TODO: Validar ownership
        
        use_case = UpdateComponentStateUseCase(db)
        response = await use_case.execute(componente_id)
        
        await db.commit()
        
        return ApiResponse(
            success=True,
            message=(
                f"Estado actualizado: {response.state.value}"
                if hasattr(response, 'state') else "Estado procesado"
            ),
            data=response
        )
        
    except NotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error actualizando estado de componente {componente_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )


# ==================== STATS ====================

@router.get(
    "/motos/{moto_id}/stats",
    response_model=ApiResponse[SensorStatsResponse]
)
async def get_sensor_stats(
    moto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas de sensores de una moto.
    
    Incluye:
    - Total de sensores
    - Sensores por estado
    - Total de lecturas
    - Sensores activos
    """
    try:
        # TODO: Validar ownership
        # TODO: Feature gating para premium
        
        use_case = GetSensorStatsUseCase(db)
        stats = await use_case.execute(moto_id)
        
        return ApiResponse(
            success=True,
            message="Estadísticas obtenidas exitosamente",
            data=stats
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de moto {moto_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno"
        )
