"""
Validadores para el módulo de sensores.

Funciones de validación reutilizables para:
- Existencia de entidades relacionadas (motos, templates, componentes)
- Esquemas JSONB (config, valor)
- Valores en rango de umbrales
- Ownership y permisos

Incluye logging detallado para debugging y auditoría.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SensorTemplate, Sensor
from ..motos.models import Moto, MotoComponente
from ..shared.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# ============================================
# VALIDADORES DE EXISTENCIA
# ============================================

async def validate_moto_exists(session: AsyncSession, moto_id: int) -> Moto:
    """
    Validar que una moto existe.
    
    Args:
        session: Sesión de base de datos
        moto_id: ID de la moto
        
    Returns:
        Moto encontrada
        
    Raises:
        NotFoundError: Si la moto no existe
    """
    try:
        result = await session.execute(
            select(Moto).where(Moto.id == moto_id)
        )
        moto = result.scalar_one_or_none()
        
        if not moto:
            logger.warning(f"Moto {moto_id} no encontrada")
            raise NotFoundError(f"Moto con ID {moto_id} no encontrada")
        
        logger.debug(f"Moto {moto_id} validada: {moto.nombre_completo}")
        return moto
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error validando existencia de moto {moto_id}: {e}")
        raise ValidationError(f"Error al validar moto: {str(e)}")


async def validate_template_exists(session: AsyncSession, template_id: UUID) -> SensorTemplate:
    """
    Validar que una plantilla de sensor existe.
    
    Args:
        session: Sesión de base de datos
        template_id: ID de la plantilla
        
    Returns:
        Plantilla encontrada
        
    Raises:
        NotFoundError: Si la plantilla no existe
    """
    try:
        result = await session.execute(
            select(SensorTemplate).where(SensorTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            logger.warning(f"Template {template_id} no encontrado")
            raise NotFoundError(f"Template con ID {template_id} no encontrado")
        
        logger.debug(f"Template {template_id} validado: {template.name}")
        return template
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error validando existencia de template {template_id}: {e}")
        raise ValidationError(f"Error al validar template: {str(e)}")


async def validate_componente_exists(session: AsyncSession, componente_id: UUID) -> MotoComponente:
    """
    Validar que un componente existe.
    
    Args:
        session: Sesión de base de datos
        componente_id: ID del componente
        
    Returns:
        Componente encontrado
        
    Raises:
        NotFoundError: Si el componente no existe
    """
    try:
        result = await session.execute(
            select(MotoComponente).where(MotoComponente.id == componente_id)
        )
        componente = result.scalar_one_or_none()
        
        if not componente:
            logger.warning(f"Componente {componente_id} no encontrado")
            raise NotFoundError(f"Componente con ID {componente_id} no encontrado")
        
        logger.debug(f"Componente {componente_id} validado: {componente.tipo}")
        return componente
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error validando existencia de componente {componente_id}: {e}")
        raise ValidationError(f"Error al validar componente: {str(e)}")


async def validate_sensor_exists(session: AsyncSession, sensor_id: UUID) -> Sensor:
    """
    Validar que un sensor existe.
    
    Args:
        session: Sesión de base de datos
        sensor_id: ID del sensor
        
    Returns:
        Sensor encontrado
        
    Raises:
        NotFoundError: Si el sensor no existe
    """
    try:
        result = await session.execute(
            select(Sensor).where(Sensor.id == sensor_id)
        )
        sensor = result.scalar_one_or_none()
        
        if not sensor:
            logger.warning(f"Sensor {sensor_id} no encontrado")
            raise NotFoundError(f"Sensor con ID {sensor_id} no encontrado")
        
        logger.debug(f"Sensor {sensor_id} validado: {sensor.tipo}")
        return sensor
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error validando existencia de sensor {sensor_id}: {e}")
        raise ValidationError(f"Error al validar sensor: {str(e)}")


# ============================================
# VALIDADORES DE OWNERSHIP
# ============================================

async def validate_sensor_belongs_to_moto(
    session: AsyncSession,
    sensor_id: UUID,
    moto_id: int
) -> bool:
    """
    Validar que un sensor pertenece a una moto específica.
    
    Args:
        session: Sesión de base de datos
        sensor_id: ID del sensor
        moto_id: ID de la moto
        
    Returns:
        True si el sensor pertenece a la moto
        
    Raises:
        ValidationError: Si el sensor no pertenece a la moto
    """
    try:
        sensor = await validate_sensor_exists(session, sensor_id)
        
        if sensor.moto_id != moto_id:
            logger.warning(
                f"Sensor {sensor_id} no pertenece a moto {moto_id} "
                f"(pertenece a moto {sensor.moto_id})"
            )
            raise ValidationError(
                f"Sensor {sensor_id} no pertenece a la moto especificada"
            )
        
        logger.debug(f"Sensor {sensor_id} validado como perteneciente a moto {moto_id}")
        return True
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error validando ownership de sensor {sensor_id}: {e}")
        raise ValidationError(f"Error al validar ownership: {str(e)}")


async def validate_componente_belongs_to_moto(
    session: AsyncSession,
    componente_id: UUID,
    moto_id: int
) -> bool:
    """
    Validar que un componente pertenece a una moto específica.
    
    Args:
        session: Sesión de base de datos
        componente_id: ID del componente
        moto_id: ID de la moto
        
    Returns:
        True si el componente pertenece a la moto
        
    Raises:
        ValidationError: Si el componente no pertenece a la moto
    """
    try:
        componente = await validate_componente_exists(session, componente_id)
        
        if componente.moto_id != moto_id:
            logger.warning(
                f"Componente {componente_id} no pertenece a moto {moto_id} "
                f"(pertenece a moto {componente.moto_id})"
            )
            raise ValidationError(
                f"Componente {componente_id} no pertenece a la moto especificada"
            )
        
        logger.debug(f"Componente {componente_id} validado como perteneciente a moto {moto_id}")
        return True
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error validando ownership de componente {componente_id}: {e}")
        raise ValidationError(f"Error al validar ownership: {str(e)}")


# ============================================
# VALIDADORES DE ESQUEMAS JSONB
# ============================================

def validate_config_schema(config: Dict[str, Any]) -> bool:
    """
    Validar esquema básico de config JSONB.
    
    Campos opcionales comunes:
    - thresholds: {min: float, max: float}
    - calibration_offset: float
    - enabled: bool
    - frequency_ms: int
    
    Args:
        config: Diccionario de configuración
        
    Returns:
        True si el esquema es válido
        
    Raises:
        ValidationError: Si el esquema es inválido
    """
    try:
        if not isinstance(config, dict):
            raise ValidationError("Config debe ser un diccionario")
        
        # Validar thresholds si existen
        if "thresholds" in config:
            thresholds = config["thresholds"]
            if not isinstance(thresholds, dict):
                raise ValidationError("thresholds debe ser un diccionario")
            
            if "min" in thresholds and "max" in thresholds:
                min_val = thresholds["min"]
                max_val = thresholds["max"]
                
                if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
                    raise ValidationError("thresholds min/max deben ser números")
                
                if min_val >= max_val:
                    raise ValidationError("threshold min debe ser menor que max")
                    
                logger.debug(f"Thresholds validados: min={min_val}, max={max_val}")
        
        # Validar calibration_offset si existe
        if "calibration_offset" in config:
            offset = config["calibration_offset"]
            if not isinstance(offset, (int, float)):
                raise ValidationError("calibration_offset debe ser un número")
        
        # Validar enabled si existe
        if "enabled" in config:
            if not isinstance(config["enabled"], bool):
                raise ValidationError("enabled debe ser un booleano")
        
        # Validar frequency_ms si existe
        if "frequency_ms" in config:
            freq = config["frequency_ms"]
            if not isinstance(freq, int) or freq <= 0:
                raise ValidationError("frequency_ms debe ser un entero positivo")
        
        logger.debug("Config schema validado correctamente")
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validando config schema: {e}")
        raise ValidationError(f"Error al validar config: {str(e)}")


def validate_valor_schema(valor: Dict[str, Any]) -> bool:
    """
    Validar esquema básico de valor JSONB.
    
    Campos requeridos:
    - value: number (el valor de la lectura)
    - unit: string (unidad de medida)
    
    Campos opcionales:
    - raw: number (valor crudo sin procesar)
    
    Args:
        valor: Diccionario con el valor de la lectura
        
    Returns:
        True si el esquema es válido
        
    Raises:
        ValidationError: Si el esquema es inválido
    """
    try:
        if not isinstance(valor, dict):
            raise ValidationError("Valor debe ser un diccionario")
        
        # Validar campos requeridos
        if "value" not in valor:
            raise ValidationError("Campo 'value' es requerido en valor")
        
        if not isinstance(valor["value"], (int, float)):
            raise ValidationError("Campo 'value' debe ser un número")
        
        if "unit" not in valor:
            raise ValidationError("Campo 'unit' es requerido en valor")
        
        if not isinstance(valor["unit"], str):
            raise ValidationError("Campo 'unit' debe ser una cadena")
        
        # Validar raw si existe
        if "raw" in valor:
            if not isinstance(valor["raw"], (int, float)):
                raise ValidationError("Campo 'raw' debe ser un número")
        
        logger.debug(f"Valor schema validado: {valor['value']} {valor['unit']}")
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validando valor schema: {e}")
        raise ValidationError(f"Error al validar valor: {str(e)}")


# ============================================
# VALIDADORES DE VALORES EN RANGO
# ============================================

def validate_valor_in_range(
    valor: float,
    thresholds: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validar si un valor está dentro de umbrales y calcular severidad.
    
    Args:
        valor: Valor a validar
        thresholds: Diccionario con min y max (opcional)
        
    Returns:
        Diccionario con:
        - in_range: bool
        - severidad: str (ok, low, medium, high, critical)
        - deviation: float (porcentaje de desviación)
        
    Raises:
        ValidationError: Si los parámetros son inválidos
    """
    try:
        if not isinstance(valor, (int, float)):
            raise ValidationError("Valor debe ser un número")
        
        # Si no hay umbrales, todo es válido
        if not thresholds or "min" not in thresholds or "max" not in thresholds:
            logger.debug("No hay umbrales definidos, valor considerado OK")
            return {
                "in_range": True,
                "severidad": "ok",
                "deviation": 0.0
            }
        
        min_val = thresholds["min"]
        max_val = thresholds["max"]
        range_size = max_val - min_val
        
        # Calcular desviación
        if valor < min_val:
            deviation = ((min_val - valor) / range_size) * 100
            in_range = False
        elif valor > max_val:
            deviation = ((valor - max_val) / range_size) * 100
            in_range = False
        else:
            deviation = 0.0
            in_range = True
        
        # Calcular severidad basada en desviación
        if in_range:
            severidad = "ok"
        elif deviation <= 10:
            severidad = "low"
        elif deviation <= 25:
            severidad = "medium"
        elif deviation <= 50:
            severidad = "high"
        else:
            severidad = "critical"
        
        result = {
            "in_range": in_range,
            "severidad": severidad,
            "deviation": round(deviation, 2)
        }
        
        if not in_range:
            logger.warning(
                f"Valor {valor} fuera de rango [{min_val}, {max_val}], "
                f"desviación: {deviation:.2f}%, severidad: {severidad}"
            )
        else:
            logger.debug(f"Valor {valor} dentro de rango [{min_val}, {max_val}]")
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error validando valor en rango: {e}")
        raise ValidationError(f"Error al validar rango: {str(e)}")
