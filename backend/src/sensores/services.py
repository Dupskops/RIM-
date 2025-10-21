"""
Servicios de lógica de negocio para sensores.
"""
from datetime import datetime
from typing import Optional

from .models import Sensor, LecturaSensor, EstadoSensor
from .validators import is_valor_fuera_rango, get_sensor_unit
from ..shared.utils import clamp, safe_divide, percentage


class SensorService:
    """Servicio con lógica de negocio para sensores."""
    
    @staticmethod
    def prepare_sensor_data(
        moto_id: int,
        tipo: str,
        codigo: str,
        nombre: Optional[str] = None,
        ubicacion: Optional[str] = None,
        frecuencia_lectura: int = 5,
        umbral_min: Optional[float] = None,
        umbral_max: Optional[float] = None,
        fabricante: Optional[str] = None,
        modelo: Optional[str] = None,
        version_firmware: Optional[str] = None,
        notas: Optional[str] = None
    ) -> dict:
        """
        Prepara los datos de un sensor para creación.
        
        Args:
            moto_id: ID de la moto
            tipo: Tipo de sensor
            codigo: Código único
            nombre: Nombre del sensor
            ubicacion: Ubicación física
            frecuencia_lectura: Frecuencia en segundos
            umbral_min: Umbral mínimo
            umbral_max: Umbral máximo
            fabricante: Fabricante
            modelo: Modelo
            version_firmware: Versión del firmware
            notas: Notas
            
        Returns:
            Diccionario con datos preparados
        """
        return {
            "moto_id": moto_id,
            "tipo": tipo,
            "codigo": codigo,
            "nombre": nombre,
            "ubicacion": ubicacion,
            "estado": EstadoSensor.ACTIVE,
            "frecuencia_lectura": frecuencia_lectura,
            "umbral_min": umbral_min,
            "umbral_max": umbral_max,
            "fabricante": fabricante,
            "modelo": modelo,
            "version_firmware": version_firmware,
            "notas": notas
        }
    
    @staticmethod
    def prepare_lectura_data(
        sensor_id: int,
        sensor_tipo: str,
        valor: float,
        timestamp_lectura: datetime,
        umbral_min: Optional[float] = None,
        umbral_max: Optional[float] = None,
        metadata_json: Optional[str] = None
    ) -> dict:
        """
        Prepara los datos de una lectura para creación.
        
        Args:
            sensor_id: ID del sensor
            sensor_tipo: Tipo de sensor
            valor: Valor leído
            timestamp_lectura: Timestamp de la lectura
            umbral_min: Umbral mínimo del sensor
            umbral_max: Umbral máximo del sensor
            metadata_json: Metadata adicional
            
        Returns:
            Diccionario con datos preparados
        """
        # Determinar unidad
        unidad = get_sensor_unit(sensor_tipo)
        
        # Verificar si está fuera de rango
        fuera_rango = is_valor_fuera_rango(sensor_tipo, valor)
        
        # Verificar si se debe generar alerta
        alerta_generada = False
        if umbral_min is not None and valor < umbral_min:
            alerta_generada = True
        if umbral_max is not None and valor > umbral_max:
            alerta_generada = True
        
        return {
            "sensor_id": sensor_id,
            "valor": valor,
            "unidad": unidad,
            "timestamp_lectura": timestamp_lectura,
            "fuera_rango": fuera_rango,
            "alerta_generada": alerta_generada,
            "metadata_json": metadata_json
        }
    
    @staticmethod
    def should_generate_alert(
        valor: float,
        umbral_min: Optional[float],
        umbral_max: Optional[float]
    ) -> tuple[bool, Optional[str]]:
        """
        Determina si se debe generar una alerta.
        
        Args:
            valor: Valor leído
            umbral_min: Umbral mínimo
            umbral_max: Umbral máximo
            
        Returns:
            (debe_alertar, tipo_umbral_violado)
        """
        if umbral_min is not None and valor < umbral_min:
            return True, "min"
        
        if umbral_max is not None and valor > umbral_max:
            return True, "max"
        
        return False, None
    
    @staticmethod
    def get_alert_severity(
        valor: float,
        umbral_min: Optional[float],
        umbral_max: Optional[float],
        tipo_sensor: str
    ) -> str:
        """
        Calcula la severidad de una alerta basada en el valor y umbrales.
        
        Args:
            valor: Valor leído
            umbral_min: Umbral mínimo
            umbral_max: Umbral máximo
            tipo_sensor: Tipo de sensor
            
        Returns:
            Nivel de severidad: "info", "warning", "critical"
        """
        if umbral_min is None and umbral_max is None:
            return "info"
        
        # Calcular desviación porcentual usando safe_divide
        if umbral_min is not None and valor < umbral_min:
            # Desviación por debajo del mínimo
            deviation_pct = safe_divide((umbral_min - valor) * 100, umbral_min, 0)
            
            if deviation_pct > 30:
                return "critical"
            elif deviation_pct > 15:
                return "warning"
            else:
                return "info"
        
        if umbral_max is not None and valor > umbral_max:
            # Desviación por encima del máximo
            deviation_pct = safe_divide((valor - umbral_max) * 100, umbral_max, 0)
            
            if deviation_pct > 30:
                return "critical"
            elif deviation_pct > 15:
                return "warning"
            else:
                return "info"
        
        return "info"
    
    @staticmethod
    def can_modify_sensor(sensor: Sensor) -> tuple[bool, str]:
        """
        Verifica si un sensor puede ser modificado.
        
        Args:
            sensor: Sensor a verificar
            
        Returns:
            (puede_modificar, mensaje_error)
        """
        if sensor.deleted_at is not None:
            return False, "El sensor está eliminado"
        
        if sensor.estado == EstadoSensor.MAINTENANCE:
            return False, "El sensor está en mantenimiento, no puede ser modificado"
        
        return True, ""
    
    @staticmethod
    def can_delete_sensor(sensor: Sensor) -> tuple[bool, str]:
        """
        Verifica si un sensor puede ser eliminado.
        
        Args:
            sensor: Sensor a verificar
            
        Returns:
            (puede_eliminar, mensaje_error)
        """
        if sensor.deleted_at is not None:
            return False, "El sensor ya está eliminado"
        
        return True, ""
