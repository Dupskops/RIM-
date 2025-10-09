"""
Rutas HTTP para el módulo de ML.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Annotated, Dict, Any

from src.config.database import get_db
from src.shared.base_models import (
    ApiResponse,
    PaginatedResponse,
    PaginationParams,
    create_success_response,
    create_paginated_response
)
from src.ml.schemas import (
    PrediccionFallaRequest,
    PrediccionAnomaliaRequest,
    PrediccionResponse,
    PrediccionValidacionRequest,
    PrediccionFilterParams,
    EstadisticasPrediccionesResponse,
    ModeloInfoResponse
)
from src.ml.use_cases import (
    PredecirFallaUseCase,
    DetectarAnomaliaUseCase,
    ValidarPrediccionUseCase,
    ObtenerPrediccionesUseCase,
    ObtenerEstadisticasUseCase,
    ObtenerModeloInfoUseCase
)
from src.ml.services import MLService, EntrenamientoService
from src.ml.repositories import PrediccionRepository, EntrenamientoRepository
from src.shared.event_bus import event_bus

router = APIRouter()


# ============= DEPENDENCIES =============

def get_ml_service() -> MLService:
    """Dependencia: Servicio de ML."""
    prediccion_repo = PrediccionRepository()
    entrenamiento_repo = EntrenamientoRepository()
    return MLService(prediccion_repo, entrenamiento_repo)


def get_entrenamiento_service() -> EntrenamientoService:
    """Dependencia: Servicio de entrenamientos."""
    return EntrenamientoService(EntrenamientoRepository())


def get_event_bus():
    """Dependencia: Event Bus real."""
    return event_bus


# ============= ENDPOINTS =============

@router.post(
    "/predict/fault",
    response_model=ApiResponse[PrediccionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Predecir falla",
    description="Realiza predicción de falla usando modelo de ML"
)
async def predecir_falla(
    request: PrediccionFallaRequest,
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service),
    event_bus = Depends(get_event_bus)
) -> ApiResponse[PrediccionResponse]:
    """Endpoint para predecir fallas en motocicleta."""
    use_case = PredecirFallaUseCase(ml_service, event_bus)
    
    try:
        prediccion = await use_case.execute(db, request)
        return create_success_response(
            data=prediccion,
            message="Predicción de falla generada exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en predicción: {str(e)}"
        )


@router.post(
    "/predict/anomaly",
    response_model=ApiResponse[Optional[PrediccionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Detectar anomalía",
    description="Detecta anomalías en datos de sensores"
)
async def detectar_anomalia(
    request: PrediccionAnomaliaRequest,
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service),
    event_bus = Depends(get_event_bus)
) -> ApiResponse[Optional[PrediccionResponse]]:
    """Endpoint para detectar anomalías."""
    use_case = DetectarAnomaliaUseCase(ml_service, event_bus)
    
    try:
        prediccion = await use_case.execute(db, request)
        if prediccion:
            return create_success_response(
                data=prediccion,
                message="Anomalía detectada"
            )
        else:
            return create_success_response(
                data=None,
                message="No se detectaron anomalías"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en detección: {str(e)}"
        )


@router.put(
    "/predictions/{prediccion_id}/validate",
    response_model=ApiResponse[PrediccionResponse],
    summary="Validar predicción",
    description="Marca una predicción como correcta o incorrecta"
)
async def validar_prediccion(
    prediccion_id: int,
    request: PrediccionValidacionRequest,
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service),
    event_bus = Depends(get_event_bus)
) -> ApiResponse[PrediccionResponse]:
    """Endpoint para validar predicciones."""
    use_case = ValidarPrediccionUseCase(ml_service, event_bus)
    
    try:
        prediccion = await use_case.execute(db, prediccion_id, request)
        
        if not prediccion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Predicción {prediccion_id} no encontrada"
            )
        
        estado_texto = "confirmada" if request.es_correcta else "falsa"
        return create_success_response(
            data=prediccion,
            message=f"Predicción marcada como {estado_texto}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando predicción: {str(e)}"
        )


@router.get(
    "/predictions/moto/{moto_id}",
    response_model=PaginatedResponse[PrediccionResponse],
    summary="Obtener predicciones por moto",
    description="Lista todas las predicciones de una motocicleta"
)
async def obtener_predicciones_moto(
    moto_id: int,
    filters: Annotated[PrediccionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service)
) -> PaginatedResponse[PrediccionResponse]:
    """Endpoint para obtener predicciones de una moto."""
    use_case = ObtenerPrediccionesUseCase(ml_service)
    
    try:
        # Forzar el filtro por moto_id
        filters.moto_id = moto_id
        
        predicciones, total = await use_case.execute(db, filters, pagination)
        
        # Construir respuestas
        predicciones_response = [
            PrediccionResponse.model_validate(p) for p in predicciones
        ]
        
        return create_paginated_response(
            items=predicciones_response,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo predicciones: {str(e)}"
        )


@router.get(
    "/predictions/usuario/{usuario_id}",
    response_model=PaginatedResponse[PrediccionResponse],
    summary="Obtener predicciones por usuario",
    description="Lista todas las predicciones de un usuario"
)
async def obtener_predicciones_usuario(
    usuario_id: int,
    filters: Annotated[PrediccionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service)
) -> PaginatedResponse[PrediccionResponse]:
    """Endpoint para obtener predicciones de un usuario."""
    use_case = ObtenerPrediccionesUseCase(ml_service)
    
    try:
        # Forzar el filtro por usuario_id
        filters.usuario_id = usuario_id
        
        predicciones, total = await use_case.execute(db, filters, pagination)
        
        # Construir respuestas
        predicciones_response = [
            PrediccionResponse.model_validate(p) for p in predicciones
        ]
        
        return create_paginated_response(
            message="Predicciones obtenidas exitosamente",
            data=predicciones_response,
            page=pagination.page,
            per_page=pagination.limit,
            total_items=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo predicciones: {str(e)}"
        )


@router.get(
    "/predictions/criticas",
    response_model=PaginatedResponse[PrediccionResponse],
    summary="Obtener predicciones críticas",
    description="Lista predicciones críticas (confianza >= 0.85)"
)
async def obtener_predicciones_criticas(
    filters: Annotated[PrediccionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service)
) -> PaginatedResponse[PrediccionResponse]:
    """Endpoint para obtener predicciones críticas."""
    use_case = ObtenerPrediccionesUseCase(ml_service)
    
    try:
        # Forzar el filtro de críticas
        filters.es_critica = True
        
        predicciones, total = await use_case.execute(db, filters, pagination)
        
        # Construir respuestas
        predicciones_response = [
            PrediccionResponse.model_validate(p) for p in predicciones
        ]
        
        return create_paginated_response(
            message="Predicciones críticas obtenidas exitosamente",
            data=predicciones_response,
            page=pagination.page,
            per_page=pagination.limit,
            total_items=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo predicciones críticas: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=ApiResponse[EstadisticasPrediccionesResponse],
    summary="Obtener estadísticas",
    description="Estadísticas generales de predicciones"
)
async def obtener_estadisticas(
    moto_id: Optional[int] = Query(None),
    usuario_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    ml_service: MLService = Depends(get_ml_service)
) -> ApiResponse[EstadisticasPrediccionesResponse]:
    """Endpoint para obtener estadísticas."""
    use_case = ObtenerEstadisticasUseCase(ml_service)
    
    try:
        estadisticas = await use_case.execute(db, moto_id, usuario_id)
        return create_success_response(
            data=estadisticas,
            message="Estadísticas de predicciones obtenidas exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get(
    "/models/{nombre_modelo}/info",
    response_model=ApiResponse[ModeloInfoResponse],
    summary="Información de modelo",
    description="Obtiene información del modelo en producción"
)
async def obtener_info_modelo(
    nombre_modelo: str,
    db: AsyncSession = Depends(get_db),
    entrenamiento_service: EntrenamientoService = Depends(get_entrenamiento_service)
) -> ApiResponse[ModeloInfoResponse]:
    """Endpoint para obtener información de modelo."""
    use_case = ObtenerModeloInfoUseCase(entrenamiento_service)
    
    try:
        info = await use_case.execute(db, nombre_modelo)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Modelo {nombre_modelo} no encontrado"
            )
        
        return create_success_response(
            data=ModeloInfoResponse(**info),
            message=f"Información del modelo {nombre_modelo} obtenida exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo información: {str(e)}"
        )


@router.get(
    "/models/status",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Estado de modelos",
    description="Estado general de los modelos ML"
)
async def estado_modelos() -> ApiResponse[Dict[str, Any]]:
    """Endpoint para verificar estado de modelos."""
    from src.ml.inference import fault_predictor, anomaly_detector, FAULT_PREDICTOR_PATH, ANOMALY_DETECTOR_PATH
    
    data = {
        "fault_predictor": {
            "nombre": fault_predictor.model_name,
            "version": fault_predictor.version,
            "path": str(FAULT_PREDICTOR_PATH),
            "existe": FAULT_PREDICTOR_PATH.exists(),
            "cargado": fault_predictor.model_loader.get_model(fault_predictor.model_name) is not None
        },
        "anomaly_detector": {
            "nombre": anomaly_detector.model_name,
            "version": anomaly_detector.version,
            "path": str(ANOMALY_DETECTOR_PATH),
            "existe": ANOMALY_DETECTOR_PATH.exists(),
            "cargado": anomaly_detector.model_loader.get_model(anomaly_detector.model_name) is not None
        }
    }
    
    return create_success_response(
        data=data,
        message="Estado de modelos ML obtenido exitosamente"
    )
