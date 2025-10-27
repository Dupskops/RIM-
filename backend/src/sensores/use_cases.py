"""
Casos de uso para el módulo de sensores.

Orquesta la lógica completa de negocio coordinando:
- Validators: Validación de datos y existencia
- Repositories: Acceso a base de datos
- Services: Lógica de negocio pura
- Events: Emisión de eventos de dominio

Cada use case sigue el patrón:
1. Validar entrada
2. Ejecutar lógica de negocio
3. Persistir cambios
4. Emitir eventos
5. Retornar resultado

Incluye logging exhaustivo y manejo robusto de errores.
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SensorTemplate, Sensor, Lectura, SensorState
from ..motos.models import Moto, MotoComponente, ComponentState
from .schemas import (
    SensorTemplateCreate, SensorTemplateUpdate, SensorTemplateRead,
    CreateSensorRequest, UpdateSensorRequest, SensorRead,
    CreateLecturaRequest, LecturaRead,
    SensorStatsResponse, ComponentStateResponse
)
from .repositories import (
    SensorTemplateRepository,
    MotoComponenteRepository,
    SensorRepository,
    LecturaRepository
)
from .validators import (
    validate_moto_exists,
    validate_template_exists,
    validate_componente_exists,
    validate_sensor_exists,
    validate_sensor_belongs_to_moto,
    validate_componente_belongs_to_moto,
    validate_config_schema,
    validate_valor_schema,
    validate_valor_in_range
)
from .services import SensorService
from .events import (
    emit_sensor_registered,
    emit_lectura_registrada,
    emit_componente_estado_actualizado,
    emit_alerta_sensor
)
from ..shared.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class CreateSensorTemplateUseCase:
    """Caso de uso: Crear plantilla de sensor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_repo = SensorTemplateRepository(db)

    async def execute(self, data: SensorTemplateCreate) -> SensorTemplateRead:
        """
        Crear nueva plantilla de sensor.
        
        Args:
            data: Datos de la plantilla
            
        Returns:
            Plantilla creada
        """
        try:
            logger.info(f"Creando template de sensor: modelo={data.modelo}")
            
            # Crear template
            template_data = {
                "modelo": data.modelo,
                "name": data.name,
                "definition": data.definition
            }
            template = await self.template_repo.create(template_data)
            
            logger.info(f"Template creado exitosamente: id={template.id}")
            
            return SensorTemplateRead.model_validate(template)
            
        except Exception as e:
            logger.error(f"Error creando template: {e}")
            raise


class GetSensorTemplateUseCase:
    """Caso de uso: Obtener plantilla de sensor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_repo = SensorTemplateRepository(db)

    async def execute(self, template_id: UUID) -> SensorTemplateRead:
        """
        Obtener plantilla por ID.
        
        Args:
            template_id: ID de la plantilla
            
        Returns:
            Plantilla encontrada
        """
        try:
            logger.debug(f"Obteniendo template: id={template_id}")
            
            template = await validate_template_exists(self.db, template_id)
            
            return SensorTemplateRead.model_validate(template)
            
        except Exception as e:
            logger.error(f"Error obteniendo template {template_id}: {e}")
            raise


class CreateSensorUseCase:
    """Caso de uso: Crear sensor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sensor_repo = SensorRepository(db)

    async def execute(
        self,
        data: CreateSensorRequest,
        correlation_id: Optional[UUID] = None
    ) -> SensorRead:
        """
        Crear nuevo sensor.
        
        Flujo:
        1. Validar moto existe
        2. Validar template existe (si se proporciona)
        3. Validar componente existe y pertenece a moto (si se proporciona)
        4. Validar schema de config
        5. Crear sensor
        6. Emitir evento
        
        Args:
            data: Datos del sensor
            correlation_id: ID de correlación para eventos
            
        Returns:
            Sensor creado
        """
        try:
            logger.info(
                f"Creando sensor: moto_id={data.moto_id}, "
                f"tipo={data.tipo}, template_id={data.template_id}"
            )
            
            # 1. Validar moto
            await validate_moto_exists(self.db, data.moto_id)
            
            # 2. Validar template (si existe)
            if data.template_id:
                await validate_template_exists(self.db, data.template_id)
            
            # 3. Validar componente (si existe)
            if data.componente_id:
                await validate_componente_belongs_to_moto(
                    self.db,
                    data.componente_id,
                    data.moto_id
                )
            
            # 4. Validar config
            if data.config:
                validate_config_schema(data.config)
            
            # 5. Crear sensor
            sensor_data = {
                "moto_id": data.moto_id,
                "template_id": data.template_id,
                "nombre": data.nombre,
                "tipo": data.tipo,
                "componente_id": data.componente_id,
                "config": data.config,
                "sensor_state": SensorState.UNKNOWN
            }
            sensor = await self.sensor_repo.create(sensor_data)
            
            # 6. Emitir evento
            await emit_sensor_registered(
                sensor_id=sensor.id,
                moto_id=sensor.moto_id,
                tipo=sensor.tipo,
                template_id=sensor.template_id,
                componente_id=sensor.componente_id,
                correlation_id=correlation_id
            )
            
            logger.info(f"Sensor creado exitosamente: id={sensor.id}")
            
            return SensorRead.model_validate(sensor)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error creando sensor: {e}")
            raise


class UpdateSensorUseCase:
    """Caso de uso: Actualizar sensor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sensor_repo = SensorRepository(db)

    async def execute(
        self,
        sensor_id: UUID,
        data: UpdateSensorRequest
    ) -> SensorRead:
        """
        Actualizar sensor existente.
        
        Args:
            sensor_id: ID del sensor
            data: Datos a actualizar
            
        Returns:
            Sensor actualizado
        """
        try:
            logger.info(f"Actualizando sensor: id={sensor_id}")
            
            # Validar sensor existe
            sensor = await validate_sensor_exists(self.db, sensor_id)
            
            # Validar config si se proporciona
            if data.config is not None:
                validate_config_schema(data.config)
            
            # Actualizar
            update_data = data.model_dump(exclude_unset=True)
            sensor = await self.sensor_repo.update(sensor_id, update_data)
            
            logger.info(f"Sensor actualizado exitosamente: id={sensor_id}")
            
            return SensorRead.model_validate(sensor)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando sensor {sensor_id}: {e}")
            raise


class CreateLecturaUseCase:
    """Caso de uso: Crear lectura de sensor."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.lectura_repo = LecturaRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.service = SensorService()

    async def execute(
        self,
        data: CreateLecturaRequest,
        correlation_id: Optional[UUID] = None
    ) -> LecturaRead:
        """
        Registrar nueva lectura de sensor.
        
        Flujo:
        1. Validar sensor existe y pertenece a moto
        2. Validar schema de valor
        3. Verificar valor en rango y generar alerta si es necesario
        4. Persistir lectura
        5. Actualizar last_seen del sensor
        6. Emitir evento LecturaRegistrada
        7. Emitir evento AlertaSensor si hay violación
        
        Args:
            data: Datos de la lectura
            correlation_id: ID de correlación para eventos
            
        Returns:
            Lectura creada
        """
        try:
            logger.info(f"Registrando lectura: sensor_id={data.sensor_id}")
            
            # 1. Validar sensor
            sensor = await validate_sensor_exists(self.db, data.sensor_id)
            
            # 2. Validar valor
            validate_valor_schema(data.valor)
            
            # 3. Verificar umbrales
            alert_data = None
            if sensor.config and "thresholds" in sensor.config:
                thresholds = sensor.config["thresholds"]
                valor_numeric = data.valor.get("value")
                
                if valor_numeric is not None:
                    alert_data = self.service.check_threshold_violation(
                        valor=valor_numeric,
                        thresholds=thresholds,
                        sensor_tipo=sensor.tipo,
                        sensor_id=sensor.id
                    )
            
            # 4. Persistir lectura
            lectura_data = {
                "moto_id": sensor.moto_id,
                "sensor_id": data.sensor_id,
                "component_id": sensor.componente_id,
                "ts": data.ts,
                "valor": data.valor,
                "extra_data": data.metadata  # metadata → extra_data
            }
            lectura = await self.lectura_repo.create(lectura_data)
            
            # 5. Actualizar last_seen
            await self.sensor_repo.update_last_seen(
                sensor_id=sensor.id,
                last_value=data.valor
            )
            
            # 6. Emitir evento LecturaRegistrada
            await emit_lectura_registrada(
                lectura_id=lectura.id,
                moto_id=lectura.moto_id,
                sensor_id=lectura.sensor_id,
                ts=lectura.ts,
                valor=lectura.valor,
                component_id=lectura.component_id,
                correlation_id=correlation_id
            )
            
            # 7. Emitir alerta si es necesario
            if alert_data:
                logger.warning(
                    f"Alerta generada: sensor={sensor.id}, "
                    f"severidad={alert_data['severidad']}"
                )
                
                await emit_alerta_sensor(
                    sensor_id=sensor.id,
                    moto_id=sensor.moto_id,
                    tipo_sensor=sensor.tipo,
                    valor_actual=data.valor,
                    umbral_violado=alert_data["umbral_violado"],
                    severidad=alert_data["severidad"],
                    mensaje=alert_data["mensaje"],
                    component_id=sensor.componente_id,
                    correlation_id=correlation_id
                )
            
            logger.info(f"Lectura registrada exitosamente: id={lectura.id}")
            
            return LecturaRead.model_validate(lectura)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error registrando lectura: {e}")
            raise


class ProvisionSensorsUseCase:
    """Caso de uso: Provisionar sensores automáticamente para una moto."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_repo = SensorTemplateRepository(db)
        self.componente_repo = MotoComponenteRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.service = SensorService()

    async def execute(
        self,
        moto_id: int,
        correlation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Provisionar sensores automáticamente basados en modelo de moto.
        
        Flujo:
        1. Validar moto existe
        2. Obtener templates por modelo
        3. Agrupar templates por tipo de componente
        4. Para cada tipo de componente:
           a. Crear componente
           b. Crear sensores asociados
        5. Emitir eventos
        
        Args:
            moto_id: ID de la moto
            correlation_id: ID de correlación para eventos
            
        Returns:
            Resumen de provisión
        """
        try:
            logger.info(f"Provisionando sensores para moto: id={moto_id}")
            
            # 1. Validar moto
            moto = await validate_moto_exists(self.db, moto_id)
            
            # 2. Obtener templates por modelo
            templates = await self.template_repo.get_by_modelo(moto.modelo)
            
            if not templates:
                logger.warning(
                    f"No hay templates disponibles para modelo: {moto.modelo}"
                )
                return {
                    "componentes_creados": 0,
                    "sensores_creados": 0,
                    "templates_procesados": 0
                }
            
            # 3. Agrupar por tipo de componente
            grouped = self.service.group_templates_by_component(templates)
            
            componentes_creados = []
            sensores_creados = []
            
            # 4. Crear componentes y sensores
            for component_type, component_templates in grouped.items():
                logger.debug(
                    f"Procesando componente: tipo={component_type}, "
                    f"{len(component_templates)} templates"
                )
                
                # 4a. Crear componente
                componente_data_prep = self.service.prepare_componente_from_template(
                    template=component_templates[0],  # Usar primer template para metadata
                    moto_id=moto_id
                )
                
                componente_data = {
                    "moto_id": moto_id,
                    "tipo": componente_data_prep["tipo"],
                    "nombre": componente_data_prep["nombre"],
                    "component_state": ComponentState.UNKNOWN,
                    "extra_data": {
                        "sensor_count": len(component_templates),
                        "auto_provisioned": True
                    }
                }
                
                componente = await self.componente_repo.create(componente_data)
                
                componentes_creados.append(componente)
                logger.info(
                    f"Componente creado: id={componente.id}, tipo={componente.tipo}"
                )
                
                # 4b. Crear sensores
                for template in component_templates:
                    sensor_data = self.service.prepare_sensor_from_template(
                        template=template,
                        moto_id=moto_id,
                        componente_id=componente.id
                    )
                    
                    sensor = await self.sensor_repo.create(**sensor_data)
                    sensores_creados.append(sensor)
                    
                    # Emitir evento por cada sensor
                    await emit_sensor_registered(
                        sensor_id=sensor.id,
                        moto_id=sensor.moto_id,
                        tipo=sensor.tipo,
                        template_id=sensor.template_id,
                        componente_id=sensor.componente_id,
                        correlation_id=correlation_id,
                        metadata={"auto_provisioned": True}
                    )
                    
                    logger.debug(f"Sensor creado: id={sensor.id}, tipo={sensor.tipo}")
            
            result = {
                "componentes_creados": len(componentes_creados),
                "sensores_creados": len(sensores_creados),
                "templates_procesados": len(templates),
                "moto_id": moto_id,
                "modelo": moto.modelo
            }
            
            logger.info(
                f"Provisión completada: {result['componentes_creados']} componentes, "
                f"{result['sensores_creados']} sensores"
            )
            
            return result
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error provisionando sensores para moto {moto_id}: {e}")
            raise


class UpdateComponentStateUseCase:
    """Caso de uso: Actualizar estado de componente basado en sensores."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.componente_repo = MotoComponenteRepository(db)
        self.sensor_repo = SensorRepository(db)
        self.service = SensorService()

    async def execute(
        self,
        componente_id: UUID,
        correlation_id: Optional[UUID] = None
    ) -> ComponentStateResponse:
        """
        Actualizar estado agregado de componente.
        
        Flujo:
        1. Validar componente existe
        2. Obtener sensores del componente
        3. Calcular nuevo estado agregado
        4. Actualizar componente si cambió el estado
        5. Emitir evento si cambió
        
        Args:
            componente_id: ID del componente
            correlation_id: ID de correlación para eventos
            
        Returns:
            Estado actualizado del componente
        """
        try:
            logger.info(f"Actualizando estado de componente: id={componente_id}")
            
            # 1. Validar componente
            componente = await validate_componente_exists(self.db, componente_id)
            old_state = componente.component_state
            
            # 2. Obtener sensores
            sensores = await self.sensor_repo.get_by_componente(componente_id)
            
            # 3. Calcular nuevo estado
            new_state, aggregation_data = self.service.calculate_component_state(
                sensores=sensores
            )
            
            # 4. Actualizar si cambió
            if new_state != old_state:
                logger.info(
                    f"Estado de componente cambió: {old_state.value} → {new_state.value}"
                )
                
                await self.componente_repo.update_state(
                    componente_id=componente_id,
                    new_state=new_state,
                    aggregation_data=aggregation_data
                )
                
                # 5. Emitir evento
                sensor_contributions = {
                    UUID(sensor_id): contrib
                    for sensor_id, contrib in aggregation_data.get("sensor_contributions", {}).items()
                }
                
                await emit_componente_estado_actualizado(
                    componente_id=componente_id,
                    moto_id=componente.moto_id,
                    tipo_componente=componente.tipo,
                    old_state=old_state.value,
                    new_state=new_state.value,
                    aggregation_data=aggregation_data,
                    sensor_contributions=sensor_contributions,
                    correlation_id=correlation_id
                )
            else:
                logger.debug(
                    f"Estado de componente sin cambios: {old_state.value}"
                )
            
            return ComponentStateResponse(
                componente_id=componente_id,
                moto_id=componente.moto_id,
                tipo=componente.tipo,
                state=new_state,
                sensor_count=len(sensores),
                aggregation_data=aggregation_data,
                changed=new_state != old_state
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando estado de componente {componente_id}: {e}")
            raise


class GetSensorStatsUseCase:
    """Caso de uso: Obtener estadísticas de sensores."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sensor_repo = SensorRepository(db)
        self.lectura_repo = LecturaRepository(db)

    async def execute(self, moto_id: int) -> SensorStatsResponse:
        """
        Obtener estadísticas de sensores de una moto.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Estadísticas de sensores
        """
        try:
            logger.debug(f"Obteniendo estadísticas de sensores: moto_id={moto_id}")
            
            # Validar moto
            await validate_moto_exists(self.db, moto_id)
            
            # Obtener stats
            stats = await self.sensor_repo.get_stats(moto_id)
            
            # Contar lecturas
            total_lecturas = await self.lectura_repo.count_by_moto(moto_id)
            
            return SensorStatsResponse(
                moto_id=moto_id,
                total_sensores=stats["total_sensores"],
                sensores_por_estado=stats["sensores_por_estado"],
                total_lecturas=total_lecturas,
                sensores_activos=stats.get("sensores_activos", 0)
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de moto {moto_id}: {e}")
            raise
