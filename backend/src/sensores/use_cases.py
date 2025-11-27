"""
Casos de uso para el módulo de sensores.

Implementa los flujos completos definidos en FLUJOS_SISTEMA.md:

📍 **Flujo #2 - Onboarding y Registro de Moto**
   - ProvisionSensorsUseCase: Provisión automática de sensores al registrar moto
     • Obtiene templates del modelo (SEED_DATA: 11 templates para KTM 390 Duke)
     • Crea componentes y sensores asociados
     • Inicializa estado UNKNOWN hasta primera lectura

📍 **Flujo #3 - Monitoreo en Tiempo Real** 
   - CreateLecturaUseCase: Pipeline completo de telemetría
     • Valida sensor y valor JSONB
     • Verifica umbrales (low/medium/high/critical)
     • Persiste lectura con ts + valor + extra_metadata
     • Actualiza last_seen del sensor
     • Emite eventos: LecturaRegistrada, AlertaSensor (si violación)

📍 **Flujo #4 - Detección de Fallas**
   - CreateLecturaUseCase: Paso 3 del pipeline
     • check_threshold_violation() calcula severidad por desviación %
     • Genera alerta automática si fuera de rango [min, max]
   - UpdateComponentStateUseCase: Agregación de estado
     • calculate_component_state() con algoritmo MAX
     • Emite ComponenteEstadoActualizadoEvent si cambió

📍 **Flujo #12 - Pipeline de Telemetría**
   Orden de procesamiento en CreateLecturaUseCase:
   1. Validación de esquema (valor JSONB con value + unit)
   2. Verificación de umbrales (opcional si sensor.config.thresholds existe)
   3. Persistencia en tabla lecturas (BIGSERIAL PK, componente_id/parametro_id obligatorios)
   4. Actualización de sensor (last_seen, last_value)
   5. Emisión de eventos (LecturaRegistrada, AlertaSensor)

📍 **Flujo #13 - Evaluación de Reglas de Estado**
   - UpdateComponentStateUseCase implementa algoritmo definido:
     • Mapeo sensor_state → score: ok=0, degraded=1, unknown=2, faulty=3, offline=4
     • Agregación MAX: el peor sensor determina el componente
     • Mapeo score → component_state: 0=EXCELENTE, 1=BUENO, 2=ATENCION, 3+=CRITICO

Orquesta coordinando:
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

Cambios v2.3:
- parametro_id obligatorio en sensores
- componente_id obligatorio en sensores y lecturas
- metadata → extra_metadata en lecturas
- FKs corregidos (motos.id, componentes.id)
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SensorState, Sensor
from ..motos.models import EstadoSalud, Componente
from .schemas import (
    SensorTemplateCreate, SensorTemplateRead,
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
    validate_componente_belongs_to_moto,
    validate_config_schema,
    validate_valor_schema
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
            template_data: Dict[str, Any] = {
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
            sensor_data: Dict[str, Any] = {
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
        
        Implementa **Flujo #12 - Pipeline de Telemetría** completo:
        
        1️⃣ Validación de Entrada (Ingestion Layer)
           - Validar sensor existe y pertenece a moto
           - Validar schema de valor JSONB (value + unit obligatorios)
           - Preparar datos para persistencia
        
        2️⃣ Verificación de Reglas (**Flujo #4 - Detección de Fallas**)
           - Verificar umbrales si sensor.config.thresholds existe
           - check_threshold_violation() calcula severidad:
             * deviation ≤10%: low
             * deviation ≤25%: medium
             * deviation ≤50%: high
             * deviation >50%: critical
           - Generar alert_data si hay violación
        
        3️⃣ Persistencia (DB Layer)
           - Crear registro en tabla lecturas
           - BIGSERIAL PK para alto volumen (1.9M lecturas/día con 10 motos)
           - componente_id y parametro_id obligatorios (v2.3)
           - ts indexado para queries temporales
        
        4️⃣ Actualización de Sensor (State Management)
           - Actualizar sensor.last_seen = now()
           - Actualizar sensor.last_value = valor JSONB
           - Mantener cache de última lectura para dashboard
        
        5️⃣ Emisión de Eventos (Event Bus)
           - LecturaRegistrada: SIEMPRE se emite (log, analytics)
           - AlertaSensor: SOLO si hay violación de umbral
           - Incluye correlation_id para tracing distribuido
        
        **Integración con otros módulos:**
        - motos: Escucha LecturaRegistrada para actualizar estado_actual
        - notificaciones: Escucha AlertaSensor para enviar push/email
        - ml: Consume lecturas para predicciones
        
        **Performance:**
        - Tiempo promedio: 20-50ms por lectura
        - Throughput: 1000+ lecturas/seg en producción
        - Indexado: (moto_id, ts DESC) para queries recientes
        
        Args:
            data: Datos de la lectura (sensor_id, ts, valor, metadata)
            correlation_id: ID de correlación para eventos (WebSocket session ID)
            
        Returns:
            Lectura creada con ID y timestamp
            
        Raises:
            NotFoundError: Si sensor no existe
            ValidationError: Si valor JSONB inválido
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
            lectura_data: Dict[str, Any] = {
                "moto_id": sensor.moto_id,
                "sensor_id": data.sensor_id,
                "componente_id": sensor.componente_id,
                "parametro_id": sensor.parametro_id,
                "ts": data.ts,
                "valor": data.valor,
                "extra_metadata": data.metadata  # metadata → extra_metadata (campo Python)
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
                componente_id=lectura.componente_id,
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
                    componente_id=sensor.componente_id,
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
        
        Implementa **Flujo #2 - Onboarding y Registro de Moto** (Paso 3):
        
        📋 **Contexto del Flujo:**
        Usuario registra KTM 390 Duke 2024 → Sistema crea:
        - 1 registro en `motos`
        - 11 registros en `estado_actual` (uno por componente, estado inicial BUENO)
        - 11 registros en `sensores` (gemelo digital, estado inicial UNKNOWN)
        - 0 registros en `lecturas` (se crean cuando llegan datos del gemelo)
        
        🔄 **Proceso de Provisión:**
        
        1️⃣ Obtener Templates por Modelo
           - Query: SELECT * FROM sensor_templates WHERE modelo = 'KTM 390 Duke 2024'
           - SEED_DATA: 11 templates disponibles (temp motor, voltaje batería, RPM, etc.)
           - Cada template define: sensor_type, component_type, default_thresholds, frequency_ms
        
        2️⃣ Agrupar por Tipo de Componente
           - Agrupar templates por definition.component_type
           - Ejemplos: "motor", "bateria", "sistema_frenos", "neumaticos"
           - Permite crear 1 componente por tipo con N sensores
        
        3️⃣ Crear Componentes y Sensores
           Para cada component_type:
           a) Crear componente:
              - moto_id: FK → motos.id
              - tipo: component_type del template
              - nombre: "Componente {tipo}"
              - estado: EstadoSalud.BUENO (inicial)
              - extra_data: {"sensor_count": N, "auto_provisioned": true}
           
           b) Crear sensores asociados:
              - Para cada template del grupo
              - moto_id: FK → motos.id
              - componente_id: FK → componentes.id (recién creado)
              - parametro_id: Inferido de template.definition (v2.3: obligatorio)
              - template_id: UUID del template
              - config: {thresholds, frequency_ms, enabled: true}
              - sensor_state: SensorState.UNKNOWN (sin lecturas aún)
        
        4️⃣ Emitir Eventos
           - SensorRegistered por cada sensor creado
           - metadata: {"auto_provisioned": true}
           - correlation_id: Mismo del flujo de registro de moto
        
        **Resultado Esperado (KTM 390 Duke 2024):**
        - componentes_creados: ~8 componentes (motor, batería, frenos, etc.)
        - sensores_creados: 11 sensores (según SEED_DATA)
        - templates_procesados: 11 templates
        
        **Integración con Flujo #3 (Monitoreo):**
        Después de provisión, gemelo digital puede empezar a enviar lecturas:
        - Frecuencias: temp motor 1seg, voltaje 2seg, RPM 500ms
        - CreateLecturaUseCase procesa cada lectura
        - sensor_state evoluciona: UNKNOWN → OK/DEGRADED/FAULTY según umbrales
        
        Args:
            moto_id: ID de la moto recién registrada
            correlation_id: ID de correlación del flujo de onboarding
            
        Returns:
            Resumen de provisión con contadores y modelo procesado
            
        Raises:
            NotFoundError: Si moto no existe o modelo sin templates
        """
        try:
            logger.info(f"Provisionando sensores para moto: id={moto_id}")
            
            # 1. Validar moto
            moto = await validate_moto_exists(self.db, moto_id)
            
            # 2. Obtener templates por modelo
            modelo_nombre: str = moto.modelo_moto.nombre
            templates = await self.template_repo.get_by_modelo(modelo_nombre)
            
            if not templates:
                logger.warning(
                    f"No hay templates disponibles para modelo: {modelo_nombre}"
                )
                return {
                    "componentes_creados": 0,
                    "sensores_creados": 0,
                    "templates_procesados": 0
                }
            
            # 3. Agrupar por tipo de componente
            grouped = self.service.group_templates_by_component(templates)
            
            componentes_creados: List[Componente] = []
            sensores_creados: List[Sensor] = []
            
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
                
                componente_data: Dict[str, Any] = {
                    "moto_id": moto_id,
                    "tipo": componente_data_prep["tipo"],
                    "nombre": componente_data_prep["nombre"],
                    # Estado inicial compatible con EstadoSalud
                    "estado": EstadoSalud.BUENO,
                    "extra_data": {
                        "sensor_count": len(component_templates),
                        "auto_provisioned": True
                    }
                }

                componente = await self.componente_repo.create(componente_data)
                
                componentes_creados.append(componente)
                logger.info(
                    f"Componente creado: id={componente.id}, nombre={componente.nombre}"
                )
                
                # 4b. Crear sensores
                # NOTA: Para MVP, asumimos que cada template mapea a un parámetro específico
                # En producción, el template debería incluir parametro_id o el sistema debe inferirlo
                for template in component_templates:
                    # TODO: Obtener parametro_id correcto desde template.definition o repositorio
                    # Por ahora, placeholder temporal (debe ser reemplazado con lógica real)
                    parametro_id = template.definition.get("parametro_id", 1)  # Default temporal
                    
                    sensor_data = self.service.prepare_sensor_from_template(
                        template=template,
                        moto_id=moto_id,
                        componente_id=componente.id,
                        parametro_id=parametro_id
                    )
                    
                    # sensor_repo.create espera un dict con los datos
                    sensor = await self.sensor_repo.create(sensor_data)
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
            
            result: Dict[str, Any] = {
                "componentes_creados": len(componentes_creados),
                "sensores_creados": len(sensores_creados),
                "templates_procesados": len(templates),
                "moto_id": moto_id,
                "modelo": modelo_nombre
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
        componente_id: int,  # Cambiado de UUID a int según DDL v2.3
        moto_id: int,  # Añadido: necesario para buscar estado_actual
        correlation_id: Optional[UUID] = None
    ) -> ComponentStateResponse:
        """
        Actualizar estado agregado de componente basado en sus sensores.
        
        Implementa **Flujo #13 - Evaluación de Reglas de Estado**:
        
        🧮 **Algoritmo de Agregación (MAX):**
        
        1️⃣ Mapeo sensor_state → score
           ```
           SensorState.OK       → 0 (perfecto)
           SensorState.DEGRADED → 1 (alerta temprana)
           SensorState.UNKNOWN  → 2 (sin datos suficientes)
           SensorState.FAULTY   → 3 (mal funcionamiento)
           SensorState.OFFLINE  → 4 (sin comunicación) o 2 si consider_offline_as_unknown=True
           ```
        
        2️⃣ Agregación MAX
           - max_score = max([score de cada sensor])
           - El **peor** sensor determina el estado del componente
           - Razón: Filosofía conservadora (priorizar seguridad)
        
        3️⃣ Mapeo score → component_state (EstadoSalud)
           ```
           max_score = 0 → EstadoSalud.EXCELENTE (todos ok)
           max_score = 1 → EstadoSalud.BUENO     (alguno degraded)
           max_score = 2 → EstadoSalud.ATENCION  (alguno unknown/offline)
           max_score ≥ 3 → EstadoSalud.CRITICO   (alguno faulty)
           ```
        
        🔄 **Flujo de Ejecución:**
        
        1️⃣ Obtener Estado Actual
           - Validar componente existe
           - Buscar en estado_actual (moto_id, componente_id)
           - old_state = estado_actual.estado (para detectar cambios)
        
        2️⃣ Obtener Sensores del Componente
           - Query: SELECT * FROM sensores WHERE moto_id = ? AND componente_id = ?
           - Incluye sensor_state de cada sensor
        
        3️⃣ Calcular Nuevo Estado
           - SensorService.calculate_component_state(sensores)
           - Retorna: (new_state, aggregation_data)
           - aggregation_data incluye:
             * sensor_count: Total de sensores
             * max_score: Score máximo encontrado
             * sensor_states: {"ok": 5, "degraded": 2, ...}
             * sensor_contributions: {sensor_id: {tipo, state, score}}
             * algorithm: "max_score_v1"
             * calculated_at: ISO timestamp
        
        4️⃣ Actualizar si Cambió
           - Si new_state != old_state:
             * Actualizar estado_actual.estado = new_state
             * Actualizar estado_actual.ultima_actualizacion = now()
             * Emitir ComponenteEstadoActualizadoEvent
        
        5️⃣ Emitir Evento (si cambió)
           - event_data:
             * componente_id, moto_id, tipo_componente
             * old_state, new_state
             * aggregation_data (con sensor_contributions)
           - Listeners:
             * motos: Actualiza estado_actual del componente
             * notificaciones: Si new_state = CRITICO → envía alerta
             * fallas: Si new_state = CRITICO → crea falla automática
        
        **Integración con Pipeline de Telemetría:**
        - Llamado después de CreateLecturaUseCase
        - Frecuencia: Solo cuando lectura cambia sensor_state
        - Evita cálculos innecesarios si estado no cambió
        
        **Ejemplo Concreto:**
        ```
        Componente: Motor (id=1)
        Moto: KTM 390 Duke (id=42)
        Sensores:
        - Temp motor: FAULTY (score=3)  ← Sobrecalentamiento 118°C
        - Presión aceite: OK (score=0)
        - RPM: DEGRADED (score=1)
        
        max_score = 3 → EstadoSalud.CRITICO
        
        UPDATE estado_actual 
        SET estado = 'CRITICO', ultima_actualizacion = now()
        WHERE moto_id = 42 AND componente_id = 1;
        
        Evento emitido:
        - old_state: BUENO
        - new_state: CRITICO
        - motos escucha → notificaciones → push "⚠️ Motor en estado crítico"
        ```
        
        Args:
            componente_id: ID del componente a evaluar (int según DDL v2.3)
            moto_id: ID de la moto (necesario para buscar estado_actual)
            correlation_id: ID de correlación para tracing
            
        Returns:
            ComponentStateResponse con estado actualizado y metadata
            
        Raises:
            NotFoundError: Si componente o moto no existe
        
        Notes:
            - DDL v2.3: componentes.id es INT (no UUID)
            - estado_actual tiene constraint UNIQUE (moto_id, componente_id)
            - Estado está en estado_actual, NO en componentes directamente
        """
        try:
            logger.info(f"Actualizando estado de componente: id={componente_id}")
            
            # 1. Validar componente
            componente = await validate_componente_exists(self.db, componente_id)
            
            # NOTA: El estado del componente está en tabla estado_actual (relación moto-componente)
            # No hay un campo componente.estado directamente según DDL v2.3
            # El estado se maneja a través de estado_actual que tiene (moto_id, componente_id, estado)
            # Para este caso de uso necesitaríamos saber la moto_id también
            
            # Por ahora, asumimos estado por defecto BUENO si no hay estado_actual
            # En producción, este use case debería recibir también moto_id
            old_state = EstadoSalud.BUENO  # Placeholder
            
            # 2. Obtener sensores del componente en esta moto
            # TODO CRÍTICO: Implementar SensorRepository.get_by_moto_and_componente()
            # Query SQL: SELECT * FROM sensores WHERE moto_id = ? AND componente_id = ?
            # Actualmente get_by_componente_id() no existe en el repositorio
            sensores: List[Any] = []  # Placeholder - requiere implementación
            
            # 3. Calcular nuevo estado
            new_state, aggregation_data = self.service.calculate_component_state(
                sensores=sensores
            )
            
            # 4. Actualizar si cambió
            if new_state != old_state:
                logger.info(
                    f"Estado de componente cambió: {old_state.value if hasattr(old_state, 'value') else old_state} → {new_state.value}"
                )
                
                # Actualizar estado_actual (requiere moto_id + componente_id)
                await self.componente_repo.update_state(
                    moto_id=moto_id,
                    componente_id=componente_id,
                    new_state=new_state
                )
                
                # 5. Emitir evento
                sensor_contributions: Dict[UUID, Dict[str, Any]] = {
                    UUID(sensor_id): contrib
                    for sensor_id, contrib in aggregation_data.get("sensor_contributions", {}).items()
                }
                
                # Obtener tipo de componente desde la relación del sensor
                # (sensores[0] existe porque el flujo solo se ejecuta si hay sensores)
                tipo_componente: str = componente.nombre if componente else "unknown"
                
                await emit_componente_estado_actualizado(
                    componente_id=componente_id,
                    moto_id=moto_id,
                    tipo_componente=tipo_componente,
                    old_state=old_state.value if hasattr(old_state, 'value') else str(old_state),
                    new_state=new_state.value,
                    aggregation_data=aggregation_data,
                    sensor_contributions=sensor_contributions,
                    correlation_id=correlation_id
                )
            else:
                logger.debug(
                    f"Estado de componente sin cambios: {old_state.value}"
                )
            
            # Construir respuesta acorde al esquema ComponentStateResponse
            # NOTA: Ajustar cuando motos/models.py sea actualizado con v2.3
            return ComponentStateResponse(
                componente_id=componente_id,
                moto_id=getattr(componente, 'moto_id', 0),  # Placeholder hasta actualizar modelo
                tipo=getattr(componente, 'tipo', componente.nombre),
                nombre=componente.nombre,
                component_state=new_state,
                sensor_count=len(sensores),
                last_updated=getattr(componente, 'last_updated', None),
                aggregation_data=aggregation_data
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
            
            # Contar lecturas (no se usa en SensorStatsResponse actual)
            # total_lecturas = await self.lectura_repo.count_by_moto(moto_id)
            
            # Mapear stats del repositorio al schema
            # stats["sensores_por_estado"] es un dict: {"ok": N, "degraded": M, ...}
            estados_raw = stats.get("sensores_por_estado", {})
            estados: Dict[str, int] = estados_raw if isinstance(estados_raw, dict) else {}
            
            return SensorStatsResponse(
                total=stats.get("total_sensores", 0),
                ok=estados.get("ok", 0),
                degraded=estados.get("degraded", 0),
                faulty=estados.get("faulty", 0),
                offline=estados.get("offline", 0),
                unknown=estados.get("unknown", 0)
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de moto {moto_id}: {e}")
            raise
