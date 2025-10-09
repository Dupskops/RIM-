"""
Casos de uso del módulo de ML.
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.base_models import PaginationParams
from src.ml.services import MLService, EntrenamientoService
from src.ml.schemas import (
    PrediccionFallaRequest,
    PrediccionAnomaliaRequest,
    PrediccionResponse,
    PrediccionValidacionRequest,
    PrediccionFilterParams,
    EstadisticasPrediccionesResponse
)
from src.ml.models import Prediccion
from src.shared.event_bus import EventBus
from src.ml.events import (
    PrediccionGeneradaEvent,
    PrediccionConfirmadaEvent,
    PrediccionFalsaEvent,
    AnomaliaDetectadaEvent
)


class PredecirFallaUseCase:
    """Caso de uso: Predecir falla en motocicleta."""
    
    def __init__(self, ml_service: MLService, event_bus: EventBus):
        self.ml_service = ml_service
        self.event_bus = event_bus
    
    async def execute(
        self,
        db: AsyncSession,
        request: PrediccionFallaRequest
    ) -> PrediccionResponse:
        """Ejecuta predicción de falla."""
        # Realizar predicción
        prediccion = await self.ml_service.predecir_falla(
            db=db,
            moto_id=request.moto_id,
            usuario_id=1,  # TODO: Obtener de contexto de auth
            datos_sensor=request.datos_sensor,
            kilometraje=request.kilometraje,
            dias_ultimo_mantenimiento=request.dias_ultimo_mantenimiento
        )
        
        # Emitir evento
        evento = PrediccionGeneradaEvent(
            prediccion_id=prediccion.id,
            moto_id=prediccion.moto_id,
            usuario_id=prediccion.usuario_id,
            tipo=prediccion.tipo,
            confianza=prediccion.confianza,
            descripcion=prediccion.descripcion,
            es_critica=prediccion.confianza >= 0.85,
            datos=prediccion.resultados
        )
        await self.event_bus.publish(evento)
        
        # Si es crítica, emitir evento especial
        if prediccion.confianza >= 0.85:
            await self.event_bus.publish(evento)
        
        return PrediccionResponse.model_validate(prediccion)


class DetectarAnomaliaUseCase:
    """Caso de uso: Detectar anomalías."""
    
    def __init__(self, ml_service: MLService, event_bus: EventBus):
        self.ml_service = ml_service
        self.event_bus = event_bus
    
    async def execute(
        self,
        db: AsyncSession,
        request: PrediccionAnomaliaRequest
    ) -> Optional[PrediccionResponse]:
        """Ejecuta detección de anomalía."""
        # Detectar anomalía
        prediccion = await self.ml_service.detectar_anomalia(
            db=db,
            moto_id=request.moto_id,
            usuario_id=1,  # TODO: Obtener de contexto de auth
            datos_sensor=request.datos_sensor
        )
        
        if not prediccion:
            return None
        
        # Emitir evento de anomalía
        evento = AnomaliaDetectadaEvent(
            prediccion_id=prediccion.id,
            moto_id=prediccion.moto_id,
            usuario_id=prediccion.usuario_id,
            tipo_anomalia=prediccion.metricas.get("tipo_anomalia", "desconocida"),
            severidad=prediccion.metricas.get("severidad", "media"),
            confianza=prediccion.confianza,
            datos_sensor=prediccion.datos_entrada
        )
        await self.event_bus.publish(evento)
        
        # Si es crítica, emitir evento adicional
        if prediccion.confianza >= 0.85:
            await self.event_bus.publish(evento)
        
        return PrediccionResponse.model_validate(prediccion)


class ValidarPrediccionUseCase:
    """Caso de uso: Validar predicción."""
    
    def __init__(self, ml_service: MLService, event_bus: EventBus):
        self.ml_service = ml_service
        self.event_bus = event_bus
    
    async def execute(
        self,
        db: AsyncSession,
        prediccion_id: int,
        request: PrediccionValidacionRequest
    ) -> Optional[PrediccionResponse]:
        """Ejecuta validación de predicción."""
        # Validar predicción
        prediccion = await self.ml_service.validar_prediccion(
            db=db,
            prediccion_id=prediccion_id,
            validada_por=request.validada_por,
            es_correcta=request.es_correcta
        )
        
        if not prediccion:
            return None
        
        # Emitir evento según resultado
        if request.es_correcta:
            evento = PrediccionConfirmadaEvent(
                prediccion_id=prediccion.id,
                moto_id=prediccion.moto_id,
                usuario_id=prediccion.usuario_id,
                tipo=prediccion.tipo,
                confirmada_por=request.validada_por
            )
            await self.event_bus.publish(evento)
        else:
            evento = PrediccionFalsaEvent(
                prediccion_id=prediccion.id,
                moto_id=prediccion.moto_id,
                usuario_id=prediccion.usuario_id,
                tipo=prediccion.tipo,
                marcada_por=request.validada_por
            )
            await self.event_bus.publish(evento)
        
        return PrediccionResponse.model_validate(prediccion)


class ObtenerPrediccionesUseCase:
    """Caso de uso: Obtener predicciones."""
    
    def __init__(self, ml_service: MLService):
        self.ml_service = ml_service
    
    async def execute(
        self,
        db: AsyncSession,
        filters: PrediccionFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Prediccion], int]:
        """Obtiene predicciones con filtros y paginación."""
        from src.ml.repositories import PrediccionRepository
        
        repo = PrediccionRepository()
        
        # Aplicar filtros según lo solicitado
        if filters.es_critica:
            predicciones = await repo.get_criticas(
                db, 
                filters.moto_id, 
                filters.usuario_id
            )
            total = len(predicciones)
            # Aplicar paginación manual
            start = pagination.offset
            end = start + pagination.limit
            predicciones = predicciones[start:end]
        elif filters.moto_id:
            predicciones = await repo.get_by_moto(
                db, 
                filters.moto_id, 
                pagination.offset, 
                pagination.limit
            )
            # TODO: Implementar conteo real
            total = len(predicciones)
        elif filters.usuario_id:
            predicciones = await repo.get_by_usuario(
                db, 
                filters.usuario_id, 
                pagination.offset, 
                pagination.limit
            )
            # TODO: Implementar conteo real
            total = len(predicciones)
        else:
            # Sin filtros específicos, obtener todas
            predicciones = await repo.get_by_usuario(
                db, 
                filters.usuario_id or 0, 
                pagination.offset, 
                pagination.limit
            )
            total = len(predicciones)
        
        return predicciones, total


class ObtenerEstadisticasUseCase:
    """Caso de uso: Obtener estadísticas de predicciones."""
    
    def __init__(self, ml_service: MLService):
        self.ml_service = ml_service
    
    async def execute(
        self,
        db: AsyncSession,
        moto_id: Optional[int] = None,
        usuario_id: Optional[int] = None
    ) -> EstadisticasPrediccionesResponse:
        """Obtiene estadísticas."""
        stats = await self.ml_service.obtener_estadisticas(
            db,
            moto_id=moto_id,
            usuario_id=usuario_id
        )
        
        # Calcular por tipo y nivel
        from src.ml.repositories import PrediccionRepository
        repo = PrediccionRepository()
        
        # TODO: Implementar queries específicas para estas métricas
        por_tipo: Dict[str, int] = {}
        por_nivel: Dict[str, int] = {}
        
        return EstadisticasPrediccionesResponse(
            total_predicciones=stats["total"],
            predicciones_confirmadas=stats["confirmadas"],
            predicciones_falsas=stats["falsas"],
            predicciones_pendientes=stats["pendientes"],
            tasa_acierto=stats["tasa_acierto"],
            confianza_promedio=stats["confianza_promedio"],
            por_tipo=por_tipo,
            por_nivel_confianza=por_nivel
        )


class ObtenerModeloInfoUseCase:
    """Caso de uso: Obtener información de modelos."""
    
    def __init__(self, entrenamiento_service: EntrenamientoService):
        self.entrenamiento_service = entrenamiento_service
    
    async def execute(
        self,
        db: AsyncSession,
        nombre_modelo: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene información de un modelo."""
        modelo = await self.entrenamiento_service.obtener_modelo_activo(
            db,
            nombre_modelo
        )
        
        if not modelo:
            return None
        
        return {
            "nombre": modelo.nombre_modelo,
            "version": modelo.version,
            "tipo": modelo.tipo_modelo,
            "accuracy": modelo.accuracy,
            "f1_score": modelo.f1_score,
            "en_produccion": modelo.en_produccion,
            "fecha_entrenamiento": modelo.fecha_inicio,
            "ruta_modelo": modelo.ruta_modelo
        }
