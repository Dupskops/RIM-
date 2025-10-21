"""
Simuladores de datos para sensores IoT (testing y desarrollo).
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from ..shared.constants import TipoSensor, SENSOR_RANGES
from ..shared.utils import clamp


class SensorDataSimulator:
    """Simulador de datos realistas para sensores IoT."""
    
    @staticmethod
    def generate_realistic_value(
        tipo: TipoSensor,
        within_normal_range: bool = True,
        severity_level: str = "normal"
    ) -> float:
        """
        Genera un valor realista para un tipo de sensor.
        
        Args:
            tipo: Tipo de sensor
            within_normal_range: Si debe estar en rango normal
            severity_level: "normal", "warning", "critical", "extreme"
        
        Returns:
            Valor simulado
        """
        ranges = SENSOR_RANGES.get(tipo, {})
        min_val = ranges.get("min", 0.0)
        max_val = ranges.get("max", 100.0)
        # Si no hay rangos normales definidos, usar min/max como normales
        normal_min = ranges.get("normal_min", min_val)
        normal_max = ranges.get("normal_max", max_val)
        
        if within_normal_range:
            # Valor dentro del rango normal con pequeña variación
            center = (normal_min + normal_max) / 2
            variation = (normal_max - normal_min) / 4
            value = center + random.uniform(-variation, variation)
            
        elif severity_level == "warning":
            # Cerca del límite pero no crítico
            if random.choice([True, False]):
                # Por encima del máximo normal
                value = normal_max + random.uniform(0, (max_val - normal_max) * 0.3)
            else:
                # Por debajo del mínimo normal
                value = normal_min - random.uniform(0, (normal_min - min_val) * 0.3)
                
        elif severity_level == "critical":
            # Valor crítico pero dentro de límites físicos
            if random.choice([True, False]):
                value = normal_max + random.uniform((max_val - normal_max) * 0.3, (max_val - normal_max) * 0.7)
            else:
                value = normal_min - random.uniform((normal_min - min_val) * 0.3, (normal_min - min_val) * 0.7)
                
        else:  # extreme
            # Valor extremo en límites físicos
            if random.choice([True, False]):
                value = max_val - random.uniform(0, (max_val - normal_max) * 0.1)
            else:
                value = min_val + random.uniform(0, (normal_min - min_val) * 0.1)
        
        # Redondear según el tipo
        if tipo in [TipoSensor.TEMPERATURA_MOTOR, TipoSensor.TEMPERATURA_ACEITE]:
            value = round(value, 1)
        elif tipo in [TipoSensor.VELOCIDAD, TipoSensor.NIVEL_COMBUSTIBLE]:
            value = round(value, 0)
        else:
            value = round(value, 2)
        
        # Asegurar que el valor esté dentro de límites físicos
        return clamp(value, min_val, max_val)
    
    @staticmethod
    def generate_metadata(tipo: TipoSensor) -> dict[str, Any]:
        """
        Genera metadata realista para una lectura.
        
        Args:
            tipo: Tipo de sensor
        
        Returns:
            Diccionario de metadata
        """
        base_metadata = {
            "battery_level": round(random.uniform(3.2, 4.2), 2),
            "signal_strength": random.randint(-90, -40),
            "firmware_version": f"1.{random.randint(0, 5)}.{random.randint(0, 20)}"
        }
        
        # Metadata específica por tipo
        if tipo == TipoSensor.VIBRACIONES:
            base_metadata.update({
                "axis_x": round(random.uniform(-5, 5), 2),
                "axis_y": round(random.uniform(-5, 5), 2),
                "axis_z": round(random.uniform(-5, 5), 2),
                "frequency": round(random.uniform(10, 1000), 1)
            })
        elif tipo in [TipoSensor.GPS_LATITUD, TipoSensor.GPS_LONGITUD]:
            base_metadata.update({
                "satellites": random.randint(4, 12),
                "hdop": round(random.uniform(0.5, 2.5), 1),
                "altitude": round(random.uniform(0, 3000), 1)
            })
        elif tipo in [TipoSensor.ACELEROMETRO_X, TipoSensor.ACELEROMETRO_Y, TipoSensor.ACELEROMETRO_Z]:
            base_metadata.update({
                "tilt_angle": round(random.uniform(-45, 45), 1),
                "calibration_status": random.choice(["ok", "pending", "error"])
            })
        
        return base_metadata
    
    @staticmethod
    def simulate_sensor_reading(
        sensor_id: int,
        tipo: TipoSensor,
        scenario: str = "normal"
    ) -> dict[str, Any]:
        """
        Simula una lectura completa de sensor.
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            scenario: "normal", "warning", "critical", "extreme"
        
        Returns:
            Diccionario con datos de lectura
        """
        within_normal = scenario == "normal"
        severity = scenario if not within_normal else "normal"
        
        valor = SensorDataSimulator.generate_realistic_value(
            tipo,
            within_normal_range=within_normal,
            severity_level=severity
        )
        
        metadata = SensorDataSimulator.generate_metadata(tipo)
        
        return {
            "sensor_id": sensor_id,
            "valor": valor,
            "timestamp_lectura": datetime.now(timezone.utc).isoformat(),
            "metadata_json": metadata
        }
    
    @staticmethod
    def simulate_sensor_drift(
        current_value: float,
        target_value: float,
        step: float = 0.1
    ) -> float:
        """
        Simula una deriva gradual del sensor hacia un valor objetivo.
        
        Args:
            current_value: Valor actual
            target_value: Valor objetivo
            step: Paso de cambio (0.0-1.0)
        
        Returns:
            Nuevo valor
        """
        difference = target_value - current_value
        change = difference * step
        
        # Añadir ruido aleatorio
        noise = random.uniform(-abs(change) * 0.1, abs(change) * 0.1)
        
        return current_value + change + noise
    
    @staticmethod
    def simulate_sensor_fault(tipo: TipoSensor) -> dict[str, Any]:
        """
        Simula una falla en el sensor.
        
        Args:
            tipo: Tipo de sensor
        
        Returns:
            Diccionario con datos de falla
        """
        fault_types = [
            {"type": "disconnected", "value": None},
            {"type": "frozen", "value": 0.0},
            {"type": "out_of_range", "value": 999999.0},
            {"type": "erratic", "value": random.uniform(-1000, 1000)}
        ]
        
        fault = random.choice(fault_types)
        
        return {
            "fault_type": fault["type"],
            "valor": fault["value"],
            "timestamp_lectura": datetime.now(timezone.utc).isoformat(),
            "metadata_json": {
                "error": True,
                "error_code": random.randint(1000, 9999),
                "error_message": f"Sensor fault: {fault['type']}"
            }
        }


class SensorScenarioSimulator:
    """Simulador de escenarios completos para testing."""
    
    @staticmethod
    def simulate_normal_operation(sensor_id: int, tipo: TipoSensor, duration_seconds: int = 60) -> list[dict[str, Any]]:
        """
        Simula operación normal durante un período.
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            duration_seconds: Duración en segundos
        
        Returns:
            Lista de lecturas simuladas
        """
        readings = []
        for _ in range(duration_seconds):
            reading = SensorDataSimulator.simulate_sensor_reading(
                sensor_id,
                tipo,
                scenario="normal"
            )
            readings.append(reading)
        
        return readings
    
    @staticmethod
    def simulate_progressive_failure(sensor_id: int, tipo: TipoSensor, steps: int = 20) -> list[dict[str, Any]]:
        """
        Simula una falla progresiva del sensor.
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            steps: Número de pasos
        
        Returns:
            Lista de lecturas simuladas
        """
        readings = []
        ranges = SENSOR_RANGES.get(tipo, {})
        normal_max = ranges.get("normal_max", 100.0)
        max_val = ranges.get("max", 150.0)
        
        # Comenzar normal
        current_value = SensorDataSimulator.generate_realistic_value(tipo, True)
        target_value = max_val
        
        for i in range(steps):
            # Escenario progresivo
            if i < steps * 0.3:
                scenario = "normal"
            elif i < steps * 0.6:
                scenario = "warning"
            elif i < steps * 0.9:
                scenario = "critical"
            else:
                scenario = "extreme"
            
            # Deriva hacia el valor extremo
            current_value = SensorDataSimulator.simulate_sensor_drift(
                current_value,
                target_value,
                step=0.15
            )
            
            reading = {
                "sensor_id": sensor_id,
                "valor": round(current_value, 2),
                "timestamp_lectura": datetime.now(timezone.utc).isoformat(),
                "metadata_json": SensorDataSimulator.generate_metadata(tipo)
            }
            readings.append(reading)
        
        return readings
    
    @staticmethod
    def simulate_intermittent_failure(
        sensor_id: int,
        tipo: TipoSensor,
        cycles: int = 10
    ) -> list[dict[str, Any]]:
        """
        Simula una falla intermitente (funciona/falla/funciona).
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            cycles: Número de ciclos
        
        Returns:
            Lista de lecturas simuladas
        """
        readings = []
        
        for i in range(cycles):
            # Alternar entre normal y falla
            if i % 2 == 0:
                # Funcionamiento normal
                reading = SensorDataSimulator.simulate_sensor_reading(
                    sensor_id,
                    tipo,
                    scenario="normal"
                )
            else:
                # Falla
                reading = SensorDataSimulator.simulate_sensor_fault(tipo)
                reading["sensor_id"] = sensor_id
            
            readings.append(reading)
        
        return readings
    
    @staticmethod
    def simulate_calibration_drift(
        sensor_id: int,
        tipo: TipoSensor,
        steps: int = 30
    ) -> list[dict[str, Any]]:
        """
        Simula deriva de calibración gradual (sensor desajustándose).
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            steps: Número de pasos
        
        Returns:
            Lista de lecturas simuladas
        """
        readings = []
        ranges = SENSOR_RANGES.get(tipo, {})
        normal_min = ranges.get("normal_min", ranges.get("min", 0.0))
        normal_max = ranges.get("normal_max", ranges.get("max", 100.0))
        
        # Valor inicial normal
        current_value = (normal_min + normal_max) / 2
        # Deriva gradual hacia fuera de rango
        drift_per_step = (normal_max - normal_min) * 0.05
        
        for i in range(steps):
            # Agregar deriva acumulativa
            drift = drift_per_step * i
            value = current_value + drift + random.uniform(-drift_per_step, drift_per_step)
            
            reading = {
                "sensor_id": sensor_id,
                "valor": round(value, 2),
                "timestamp_lectura": datetime.now(timezone.utc).isoformat(),
                "metadata_json": SensorDataSimulator.generate_metadata(tipo)
            }
            readings.append(reading)
        
        return readings
    
    @staticmethod
    def simulate_daily_pattern(
        sensor_id: int,
        tipo: TipoSensor,
        hours: int = 24
    ) -> list[dict[str, Any]]:
        """
        Simula un patrón diario realista (ej: temperatura más alta al mediodía).
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            hours: Número de horas a simular
        
        Returns:
            Lista de lecturas simuladas (1 por hora)
        """
        import math
        
        readings = []
        ranges = SENSOR_RANGES.get(tipo, {})
        min_val = ranges.get("min", 0.0)
        max_val = ranges.get("max", 100.0)
        normal_min = ranges.get("normal_min", min_val)
        normal_max = ranges.get("normal_max", max_val)
        
        base_timestamp = datetime.now(timezone.utc)
        
        for hour in range(hours):
            # Usar función sinusoidal para simular patrón diario
            # Máximo a las 14:00, mínimo a las 2:00
            cycle_position = (hour - 2) / 24.0  # Desplazar para que mínimo sea a las 2AM
            sine_value = math.sin(cycle_position * 2 * math.pi)
            
            # Mapear valor sinusoidal a rango normal
            value_range = normal_max - normal_min
            value = normal_min + (value_range / 2) + (sine_value * value_range / 2)
            
            # Agregar variación aleatoria pequeña
            value += random.uniform(-value_range * 0.05, value_range * 0.05)
            
            # Asegurar límites
            value = clamp(value, min_val, max_val)
            
            reading = {
                "sensor_id": sensor_id,
                "valor": round(value, 2),
                "timestamp_lectura": (base_timestamp + timedelta(hours=hour)).isoformat(),
                "metadata_json": SensorDataSimulator.generate_metadata(tipo)
            }
            readings.append(reading)
        
        return readings
    
    @staticmethod
    def simulate_spike_anomaly(
        sensor_id: int,
        tipo: TipoSensor,
        total_readings: int = 20,
        spike_position: int = 10
    ) -> list[dict[str, Any]]:
        """
        Simula lecturas normales con un pico anómalo en posición específica.
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            total_readings: Total de lecturas
            spike_position: Posición del pico anómalo
        
        Returns:
            Lista de lecturas simuladas
        """
        readings = []
        
        for i in range(total_readings):
            if i == spike_position:
                # Generar valor extremo en el pico
                reading = SensorDataSimulator.simulate_sensor_reading(
                    sensor_id,
                    tipo,
                    scenario="extreme"
                )
            else:
                # Valores normales
                reading = SensorDataSimulator.simulate_sensor_reading(
                    sensor_id,
                    tipo,
                    scenario="normal"
                )
            
            readings.append(reading)
        
        return readings
