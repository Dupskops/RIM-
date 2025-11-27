"""
Servicios de lógica de negocio para el módulo de sensores.

Contiene la lógica pura de dominio alineada con FLUJOS_SISTEMA.md:

1. **Flujo #2 - Onboarding**: Provisión automática de sensores basada en templates
    - prepare_sensor_from_template(): Crear sensor desde plantilla
    - prepare_componente_from_template(): Crear componente desde plantilla
    - group_templates_by_component(): Agrupar templates por tipo

2. **Flujo #3 - Monitoreo en Tiempo Real**: Validación de calidad de lecturas
    - validate_reading_quality(): Calcular quality_score basado en estado del sensor
    - calculate_anomaly_score(): Detectar anomalías estadísticas

3. **Flujo #4 - Detección de Fallas**: Evaluación de reglas y umbrales
    - check_threshold_violation(): Verificar violaciones y calcular severidad
    - calculate_component_state(): Agregar estado de componente (MAX algorithm)

4. **Flujo #12 - Pipeline de Telemetría**: Transformaciones y cálculos
    - Todas las funciones participan en el pipeline de procesamiento

No depende directamente de FastAPI, solo de modelos y tipos.
Incluye logging exhaustivo y manejo robusto de errores.

Cambios v2.3:
- componente_id y parametro_id son obligatorios en sensores
- Ajustado a nuevas FKs (motos.id, componentes.id)
- Algoritmo MAX para agregación de estados (FLUJO #13)
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone

from .models import SensorTemplate, Sensor, SensorState
from ..motos.models import EstadoSalud

logger = logging.getLogger(__name__)


class SensorService:
    """Servicio de lógica de negocio para sensores."""

    @staticmethod
    def prepare_sensor_from_template(
        template: SensorTemplate,
        moto_id: int,
        componente_id: int,
        parametro_id: int
    ) -> Dict[str, Any]:
        """
        Preparar datos de sensor a partir de una plantilla.
        
        Args:
            template: Plantilla de sensor
            moto_id: ID de la moto
            componente_id: ID del componente (obligatorio en v2.3)
            parametro_id: ID del parámetro (obligatorio en v2.3)
            
        Returns:
            Diccionario con datos listos para crear sensor
        """
        try:
            definition: Dict[str, Any] = template.definition
            
            sensor_data: Dict[str, Any] = {
                "moto_id": moto_id,
                "template_id": template.id,
                "nombre": template.name,
                "tipo": definition.get("sensor_type", "unknown"),
                "componente_id": componente_id,
                "parametro_id": parametro_id,
                "config": {
                    "thresholds": definition.get("default_thresholds", {}),
                    "frequency_ms": definition.get("frequency_ms", 1000),
                    "enabled": True
                },
                "sensor_state": SensorState.UNKNOWN
            }
            
            logger.debug(
                f"Sensor preparado desde template {template.id}: "
                f"tipo={sensor_data['tipo']}, nombre={sensor_data['nombre']}"
            )
            
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error preparando sensor desde template {template.id}: {e}")
            raise ValueError(f"Error al preparar sensor: {str(e)}")

    @staticmethod
    def prepare_componente_from_template(
        template: SensorTemplate,
        moto_id: int
    ) -> Dict[str, Any]:
        """
        Preparar datos de componente a partir de una plantilla.
        
        Args:
            template: Plantilla de sensor
            moto_id: ID de la moto
            
        Returns:
            Diccionario con datos listos para crear componente
        """
        try:
            definition: Dict[str, Any] = template.definition
            component_type: str = definition.get("component_type", "unknown")
            
            componente_data: Dict[str, Any] = {
                "moto_id": moto_id,
                "tipo": component_type,
                "nombre": f"Componente {component_type}",
                # Estado inicial según EstadoSalud enum
                "estado": EstadoSalud.BUENO,
                "extra_data": {
                    "sensor_count": 0,
                    "created_from_template": str(template.id)
                }
            }
            
            logger.debug(
                f"Componente preparado desde template {template.id}: "
                f"tipo={component_type}"
            )
            
            return componente_data
            
        except Exception as e:
            logger.error(f"Error preparando componente desde template {template.id}: {e}")
            raise ValueError(f"Error al preparar componente: {str(e)}")

    @staticmethod
    def calculate_component_state(
        sensores: List[Sensor],
        consider_offline_as_unknown: bool = True
    ) -> Tuple[EstadoSalud, Dict[str, Any]]:
        """
        Calcular estado agregado de un componente basado en sus sensores.
        
        Algoritmo MVP:
        1. Mapear sensor_state a score: ok=0, degraded=1, unknown=2, faulty=3, offline=4
        2. Agregar con MAX (el peor estado determina el componente)
        3. Mapear score a component_state: 0=ok, 1=warning, 2=moderate, 3+=critical
        
        Args:
            sensores: Lista de sensores asociados al componente
            consider_offline_as_unknown: Tratar offline como unknown (menos crítico)
            
        Returns:
            Tupla (ComponentState, aggregation_data)
        """
        try:
            if not sensores:
                logger.warning("Sin sensores para calcular estado de componente")
                # No hay sensores: devolver un estado por defecto (BUENO)
                return EstadoSalud.BUENO, {
                    "sensor_count": 0,
                    "max_score": 0,
                    "sensor_states": {},
                    "algorithm": "max_score_v1"
                }
            
            # Mapeo de estados a scores
            state_scores = {
                SensorState.OK: 0,
                SensorState.DEGRADED: 1,
                SensorState.UNKNOWN: 2,
                SensorState.FAULTY: 3,
                SensorState.OFFLINE: 4 if not consider_offline_as_unknown else 2
            }
            
            # Calcular scores por sensor
            sensor_scores: List[int] = []
            state_counts: Dict[str, int] = {}
            sensor_contributions: Dict[str, Dict[str, Any]] = {}
            
            for sensor in sensores:
                score: int = state_scores.get(sensor.sensor_state, 2)
                sensor_scores.append(score)
                
                # Contar estados
                state_key: str = sensor.sensor_state.value
                state_counts[state_key] = state_counts.get(state_key, 0) + 1
                
                # Guardar contribución de cada sensor
                sensor_contributions[str(sensor.id)] = {
                    "tipo": sensor.tipo,
                    "state": sensor.sensor_state.value,
                    "score": score
                }
            
            # Agregar con MAX
            max_score: int = max(sensor_scores)
            
            # Mapear a component_state
            # Mapear scores a EstadoSalud (compatibilidad)
            component_state: EstadoSalud
            if max_score == 0:
                component_state = EstadoSalud.EXCELENTE
            elif max_score == 1:
                component_state = EstadoSalud.BUENO
            elif max_score == 2:
                component_state = EstadoSalud.ATENCION
            else:  # 3+
                component_state = EstadoSalud.CRITICO
            
            aggregation_data: Dict[str, Any] = {
                "sensor_count": len(sensores),
                "max_score": max_score,
                "sensor_states": state_counts,
                "sensor_contributions": sensor_contributions,
                "algorithm": "max_score_v1",
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(
                f"Estado de componente calculado: {component_state.value} "
                f"(max_score={max_score}, {len(sensores)} sensores)"
            )
            
            return component_state, aggregation_data
            
        except Exception as e:
            logger.error(f"Error calculando estado de componente: {e}")
            # Retornar BUENO en caso de error
            return EstadoSalud.BUENO, {
                "error": str(e),
                "sensor_count": len(sensores) if sensores else 0
            }

    @staticmethod
    def check_threshold_violation(
        valor: float,
        thresholds: Dict[str, Any],
        sensor_tipo: str,
        sensor_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Verificar si un valor viola umbrales y generar alerta.
        
        Args:
            valor: Valor a verificar
            thresholds: Diccionario con min y max
            sensor_tipo: Tipo de sensor
            sensor_id: ID del sensor
            
        Returns:
            Diccionario con alerta si hay violación, None si está en rango
        """
        try:
            if not thresholds or "min" not in thresholds or "max" not in thresholds:
                logger.debug(f"Sensor {sensor_id}: sin umbrales definidos")
                return None
            
            min_val = thresholds["min"]
            max_val = thresholds["max"]
            
            # Verificar violación
            if min_val <= valor <= max_val:
                logger.debug(f"Sensor {sensor_id}: valor {valor} dentro de rango [{min_val}, {max_val}]")
                return None
            
            # Calcular severidad
            range_size = max_val - min_val
            
            if valor < min_val:
                deviation = ((min_val - valor) / range_size) * 100
                violated = "min"
            else:  # valor > max_val
                deviation = ((valor - max_val) / range_size) * 100
                violated = "max"
            
            # Mapear desviación a severidad
            severidad: str
            if deviation <= 10:
                severidad = "low"
            elif deviation <= 25:
                severidad = "medium"
            elif deviation <= 50:
                severidad = "high"
            else:
                severidad = "critical"
            
            alert_data: Dict[str, Any] = {
                "sensor_id": str(sensor_id),
                "sensor_tipo": sensor_tipo,
                "valor_actual": valor,
                "umbral_violado": {
                    "min": min_val,
                    "max": max_val,
                    "violated": violated
                },
                "deviation_percent": round(deviation, 2),
                "severidad": severidad,
                "mensaje": (
                    f"Sensor {sensor_tipo}: valor {valor} fuera de rango "
                    f"[{min_val}, {max_val}] ({violated} violado, desviación {deviation:.1f}%)"
                )
            }
            
            logger.warning(
                f"Umbral violado - Sensor {sensor_id} ({sensor_tipo}): "
                f"valor={valor}, rango=[{min_val}, {max_val}], severidad={severidad}"
            )
            
            return alert_data
            
        except Exception as e:
            logger.error(f"Error verificando umbrales para sensor {sensor_id}: {e}")
            return None

    @staticmethod
    def group_templates_by_component(
        templates: List[SensorTemplate]
    ) -> Dict[str, List[SensorTemplate]]:
        """
        Agrupar templates por tipo de componente.
        
        Args:
            templates: Lista de plantillas
            
        Returns:
            Diccionario {component_type: [templates]}
        """
        try:
            grouped: Dict[str, List[SensorTemplate]] = {}
            
            for template in templates:
                component_type: str = template.definition.get("component_type", "unknown")
                
                if component_type not in grouped:
                    grouped[component_type] = []
                
                grouped[component_type].append(template)
            
            logger.debug(
                f"Templates agrupados: {len(grouped)} tipos de componentes, "
                f"{len(templates)} templates totales"
            )
            
            return grouped
            
        except Exception as e:
            logger.error(f"Error agrupando templates: {e}")
            return {}

    @staticmethod
    def validate_reading_quality(
        valor: Dict[str, Any],
        sensor_state: SensorState
    ) -> Dict[str, Any]:
        """
        Validar calidad de una lectura y calcular métricas.
        
        Args:
            valor: Valor JSONB de la lectura
            sensor_state: Estado actual del sensor
            
        Returns:
            Diccionario con quality_score y metadata
        """
        try:
            quality_score: float = 1.0  # Perfecto por defecto
            quality_factors: List[str] = []
            
            # Factor 1: Estado del sensor
            sensor_factor: float
            if sensor_state == SensorState.OK:
                sensor_factor = 1.0
            elif sensor_state == SensorState.DEGRADED:
                sensor_factor = 0.8
                quality_factors.append("sensor_degraded")
            elif sensor_state == SensorState.FAULTY:
                sensor_factor = 0.5
                quality_factors.append("sensor_faulty")
            elif sensor_state == SensorState.OFFLINE:
                sensor_factor = 0.0
                quality_factors.append("sensor_offline")
            else:
                sensor_factor = 0.7
                quality_factors.append("sensor_unknown")
            
            quality_score *= sensor_factor
            
            # Factor 2: Completitud de datos
            if "value" not in valor or "unit" not in valor:
                quality_score *= 0.7
                quality_factors.append("incomplete_data")
            
            # Factor 3: Quality explícito en valor (si existe)
            if "quality" in valor:
                explicit_quality = valor["quality"]
                if isinstance(explicit_quality, (int, float)) and 0 <= explicit_quality <= 1:
                    quality_score *= explicit_quality
                    quality_factors.append(f"explicit_quality_{explicit_quality}")
            
            result: Dict[str, Any] = {
                "quality_score": round(quality_score, 3),
                "quality_factors": quality_factors,
                "is_reliable": quality_score >= 0.7,
                "sensor_state": sensor_state.value
            }
            
            if quality_score < 0.7:
                logger.warning(
                    f"Lectura de baja calidad: score={quality_score:.2f}, "
                    f"factores={quality_factors}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validando calidad de lectura: {e}")
            return {
                "quality_score": 0.5,
                "quality_factors": ["error"],
                "is_reliable": False,
                "error": str(e)
            }

    @staticmethod
    def calculate_anomaly_score(
        current_value: float,
        recent_values: List[float],
        threshold_multiplier: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calcular score de anomalía simple basado en desviación estándar.
        
        MVP: Detecta anomalías estadísticas simples.
        Producción: Integrar con ML para detección más sofisticada.
        
        Args:
            current_value: Valor actual
            recent_values: Valores históricos recientes
            threshold_multiplier: Multiplicador de desviación estándar
            
        Returns:
            Diccionario con anomaly_score e is_anomaly
        """
        try:
            if len(recent_values) < 3:
                logger.debug("Insuficientes valores históricos para detectar anomalías")
                return {
                    "anomaly_score": 0.0,
                    "is_anomaly": False,
                    "reason": "insufficient_data"
                }
            
            # Calcular media y desviación estándar
            mean = sum(recent_values) / len(recent_values)
            variance = sum((x - mean) ** 2 for x in recent_values) / len(recent_values)
            std_dev = variance ** 0.5
            
            if std_dev == 0:
                logger.debug("Desviación estándar cero, no hay anomalías")
                return {
                    "anomaly_score": 0.0,
                    "is_anomaly": False,
                    "reason": "zero_variance"
                }
            
            # Calcular z-score
            z_score = abs((current_value - mean) / std_dev)
            
            # Normalizar a 0-1
            anomaly_score: float = min(z_score / (threshold_multiplier * 2), 1.0)
            
            is_anomaly: bool = z_score > threshold_multiplier
            
            result: Dict[str, Any] = {
                "anomaly_score": round(anomaly_score, 3),
                "is_anomaly": is_anomaly,
                "z_score": round(z_score, 2),
                "mean": round(mean, 2),
                "std_dev": round(std_dev, 2),
                "threshold": threshold_multiplier
            }
            
            if is_anomaly:
                logger.warning(
                    f"Anomalía detectada: valor={current_value}, "
                    f"z_score={z_score:.2f}, media={mean:.2f}, std={std_dev:.2f}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculando anomaly score: {e}")
            return {
                "anomaly_score": 0.0,
                "is_anomaly": False,
                "error": str(e)
            }
