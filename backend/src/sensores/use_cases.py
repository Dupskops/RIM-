"""
Casos de uso para sensores (Application Layer).
"""
from typing import Optional, Tuple, List
from datetime import datetime

from ..shared.exceptions import (
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    SensorException
)
from src.shared.base_models import PaginationParams

from .repositories import SensorRepository, LecturaSensorRepository
from .services import SensorService
from .models import Sensor, LecturaSensor
from .schemas import (
    CreateSensorRequest,
    UpdateSensorRequest,
    CreateLecturaRequest,
    SensorFilterParams,
    LecturaFilterParams,
    SensorResponse,
    LecturaSensorResponse,
    SensorStatsResponse
)
from .events import (
    emit_sensor_registered,
    emit_sensor_updated,
    emit_sensor_deleted,
    emit_lectura_registrada,
    emit_alerta_sensor
)


class CreateSensorUseCase:
    """Caso de uso: Crear sensor."""
    
    def __init__(self, repository: SensorRepository, service: SensorService):
        self.repository = repository
        self.service = service
    
    async def execute(self, request: CreateSensorRequest) -> SensorResponse:
        """Ejecuta el caso de uso."""
        # Verificar que no exista el código
        existing = await self.repository.get_by_codigo(request.codigo)
        if existing:
            raise ResourceAlreadyExistsException(
                "Sensor",
                f"código {request.codigo}"
            )
        
        # Preparar datos
        sensor_data = self.service.prepare_sensor_data(
            moto_id=request.moto_id,
            tipo=request.tipo,
            codigo=request.codigo,
            nombre=request.nombre,
            ubicacion=request.ubicacion,
            frecuencia_lectura=request.frecuencia_lectura,
            umbral_min=request.umbral_min,
            umbral_max=request.umbral_max,
            fabricante=request.fabricante,
            modelo=request.modelo,
            version_firmware=request.version_firmware,
            notas=request.notas
        )
        
        # Crear sensor
        sensor = await self.repository.create(sensor_data)
        
        # Emitir evento
        await emit_sensor_registered(
            sensor_id=sensor.id,
            moto_id=sensor.moto_id,
            tipo=sensor.tipo,
            codigo=sensor.codigo
        )
        
        return SensorResponse.model_validate(sensor)


class RegisterLecturaUseCase:
    """Caso de uso: Registrar lectura de sensor."""
    
    def __init__(
        self,
        sensor_repo: SensorRepository,
        lectura_repo: LecturaSensorRepository,
        service: SensorService
    ):
        self.sensor_repo = sensor_repo
        self.lectura_repo = lectura_repo
        self.service = service
    
    async def execute(self, request: CreateLecturaRequest) -> LecturaSensorResponse:
        """Ejecuta el caso de uso."""
        # Obtener sensor
        sensor = await self.sensor_repo.get_by_id(request.sensor_id)
        if not sensor:
            raise ResourceNotFoundException("Sensor", str(request.sensor_id))
        
        # Preparar lectura
        lectura_data = self.service.prepare_lectura_data(
            sensor_id=sensor.id,
            sensor_tipo=sensor.tipo,
            valor=request.valor,
            timestamp_lectura=request.timestamp_lectura,
            umbral_min=sensor.umbral_min,
            umbral_max=sensor.umbral_max,
            metadata_json=request.metadata_json
        )
        
        # Crear lectura
        lectura = await self.lectura_repo.create(lectura_data)
        
        # Actualizar última lectura del sensor
        await self.sensor_repo.update_ultima_lectura(sensor.id)
        
        # Emitir evento de lectura
        await emit_lectura_registrada(
            lectura_id=lectura.id,
            sensor_id=sensor.id,
            moto_id=sensor.moto_id,
            tipo_sensor=sensor.tipo,
            valor=lectura.valor,
            unidad=lectura.unidad,
            fuera_rango=lectura.fuera_rango
        )
        
        # Si hay alerta, emitir evento
        if lectura.alerta_generada:
            should_alert, umbral_violado = self.service.should_generate_alert(
                valor=request.valor,
                umbral_min=sensor.umbral_min,
                umbral_max=sensor.umbral_max
            )
            
            if should_alert:
                severidad = self.service.get_alert_severity(
                    valor=request.valor,
                    umbral_min=sensor.umbral_min,
                    umbral_max=sensor.umbral_max,
                    tipo_sensor=sensor.tipo
                )
                
                await emit_alerta_sensor(
                    sensor_id=sensor.id,
                    moto_id=sensor.moto_id,
                    tipo_sensor=sensor.tipo,
                    valor=request.valor,
                    umbral_violado=umbral_violado or "",
                    severidad=severidad
                )
        
        return LecturaSensorResponse.model_validate(lectura)


class GetSensorStatsUseCase:
    """Caso de uso: Obtener estadísticas de sensores."""
    
    def __init__(
        self,
        sensor_repo: SensorRepository,
        lectura_repo: LecturaSensorRepository
    ):
        self.sensor_repo = sensor_repo
        self.lectura_repo = lectura_repo
    
    async def execute(self, moto_id: Optional[int] = None) -> SensorStatsResponse:
        """Ejecuta el caso de uso."""
        stats = await self.sensor_repo.get_stats(moto_id)
        lecturas_hoy = await self.lectura_repo.count_today(moto_id)
        alertas_hoy = await self.lectura_repo.count_alerts_today(moto_id)
        ultimas = await self.lectura_repo.get_recent_lecturas(moto_id, limit=10)
        
        return SensorStatsResponse(
            total_sensores=stats["total"],
            sensores_activos=stats["activos"],
            sensores_inactivos=stats["inactivos"],
            sensores_con_error=stats["con_error"],
            lecturas_hoy=lecturas_hoy,
            alertas_hoy=alertas_hoy,
            ultimas_lecturas=[LecturaSensorResponse.model_validate(l) for l in ultimas]
        )
