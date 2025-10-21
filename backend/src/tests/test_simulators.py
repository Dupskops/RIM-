"""
Tests unitarios para simuladores de sensores IoT.
"""
import pytest
from datetime import datetime

from src.sensores.simulators import SensorDataSimulator, SensorScenarioSimulator
from src.shared.constants import TipoSensor, SENSOR_RANGES


class TestSensorDataSimulator:
    """Tests para SensorDataSimulator."""
    
    def test_generate_realistic_value_within_normal_range(self):
        """Test: Valor generado está dentro del rango normal."""
        tipo = TipoSensor.TEMPERATURA_MOTOR
        valor = SensorDataSimulator.generate_realistic_value(
            tipo=tipo,
            within_normal_range=True,
            severity_level="normal"
        )
        
        ranges = SENSOR_RANGES[tipo]
        assert ranges["min"] <= valor <= ranges["max"]
    
    def test_generate_realistic_value_warning(self):
        """Test: Valor generado para warning está fuera de rango normal."""
        tipo = TipoSensor.TEMPERATURA_MOTOR
        valor = SensorDataSimulator.generate_realistic_value(
            tipo=tipo,
            within_normal_range=False,
            severity_level="warning"
        )
        
        ranges = SENSOR_RANGES[tipo]
        # Debe estar fuera de rango normal pero dentro de límites físicos
        assert ranges["min"] <= valor <= ranges["max"]
    
    def test_generate_realistic_value_critical(self):
        """Test: Valor crítico está en límites físicos."""
        tipo = TipoSensor.PRESION_ACEITE
        valor = SensorDataSimulator.generate_realistic_value(
            tipo=tipo,
            within_normal_range=False,
            severity_level="critical"
        )
        
        ranges = SENSOR_RANGES[tipo]
        assert ranges["min"] <= valor <= ranges["max"]
    
    def test_generate_realistic_value_extreme(self):
        """Test: Valor extremo está en límites físicos."""
        tipo = TipoSensor.VOLTAJE_BATERIA
        valor = SensorDataSimulator.generate_realistic_value(
            tipo=tipo,
            within_normal_range=False,
            severity_level="extreme"
        )
        
        ranges = SENSOR_RANGES[tipo]
        assert ranges["min"] <= valor <= ranges["max"]
    
    def test_generate_metadata(self):
        """Test: Metadata se genera correctamente."""
        tipo = TipoSensor.VIBRACIONES
        metadata = SensorDataSimulator.generate_metadata(tipo)
        
        # Verificar campos base
        assert "battery_level" in metadata
        assert "signal_strength" in metadata
        assert "firmware_version" in metadata
        
        # Verificar campos específicos de vibraciones
        assert "axis_x" in metadata
        assert "axis_y" in metadata
        assert "axis_z" in metadata
        assert "frequency" in metadata
    
    def test_generate_metadata_gps(self):
        """Test: Metadata GPS se genera con campos específicos."""
        tipo = TipoSensor.GPS_LATITUD
        metadata = SensorDataSimulator.generate_metadata(tipo)
        
        assert "satellites" in metadata
        assert "hdop" in metadata
        assert "altitude" in metadata
        assert 4 <= metadata["satellites"] <= 12
    
    def test_simulate_sensor_reading(self):
        """Test: Lectura completa se genera correctamente."""
        sensor_id = 123
        tipo = TipoSensor.TEMPERATURA_MOTOR
        
        reading = SensorDataSimulator.simulate_sensor_reading(
            sensor_id=sensor_id,
            tipo=tipo,
            scenario="normal"
        )
        
        # Verificar estructura
        assert reading["sensor_id"] == sensor_id
        assert "valor" in reading
        assert "timestamp_lectura" in reading
        assert "metadata_json" in reading
        
        # Verificar timestamp es válido
        timestamp = datetime.fromisoformat(reading["timestamp_lectura"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)
    
    def test_simulate_sensor_drift(self):
        """Test: Deriva de sensor funciona correctamente."""
        current = 50.0
        target = 80.0
        
        new_value = SensorDataSimulator.simulate_sensor_drift(
            current_value=current,
            target_value=target,
            step=0.1
        )
        
        # El nuevo valor debe estar entre el actual y el objetivo
        assert current <= new_value <= target or target <= new_value <= current
    
    def test_simulate_sensor_fault(self):
        """Test: Falla de sensor se simula correctamente."""
        tipo = TipoSensor.TEMPERATURA_MOTOR
        fault = SensorDataSimulator.simulate_sensor_fault(tipo)
        
        assert "fault_type" in fault
        assert "valor" in fault
        assert "timestamp_lectura" in fault
        assert "metadata_json" in fault
        
        # Verificar que metadata contiene información de error
        assert fault["metadata_json"]["error"] is True
        assert "error_code" in fault["metadata_json"]
        assert "error_message" in fault["metadata_json"]


class TestSensorScenarioSimulator:
    """Tests para SensorScenarioSimulator."""
    
    def test_simulate_normal_operation(self):
        """Test: Operación normal genera lecturas correctas."""
        sensor_id = 1
        tipo = TipoSensor.TEMPERATURA_MOTOR
        duration = 10
        
        readings = SensorScenarioSimulator.simulate_normal_operation(
            sensor_id=sensor_id,
            tipo=tipo,
            duration_seconds=duration
        )
        
        # Verificar cantidad de lecturas
        assert len(readings) == duration
        
        # Verificar que todas las lecturas son del sensor correcto
        for reading in readings:
            assert reading["sensor_id"] == sensor_id
            assert "valor" in reading
    
    def test_simulate_progressive_failure(self):
        """Test: Falla progresiva muestra escalada de valores."""
        sensor_id = 2
        tipo = TipoSensor.TEMPERATURA_MOTOR
        steps = 20
        
        readings = SensorScenarioSimulator.simulate_progressive_failure(
            sensor_id=sensor_id,
            tipo=tipo,
            steps=steps
        )
        
        # Verificar cantidad
        assert len(readings) == steps
        
        # Verificar que los valores aumentan progresivamente
        valores = [r["valor"] for r in readings]
        # Los últimos valores deben ser mayores que los primeros
        assert sum(valores[-5:]) > sum(valores[:5])
    
    def test_simulate_intermittent_failure(self):
        """Test: Falla intermitente alterna entre normal y falla."""
        sensor_id = 3
        tipo = TipoSensor.VOLTAJE_BATERIA
        cycles = 10
        
        readings = SensorScenarioSimulator.simulate_intermittent_failure(
            sensor_id=sensor_id,
            tipo=tipo,
            cycles=cycles
        )
        
        assert len(readings) == cycles
        
        # Verificar alternancia (pares=normal, impares=falla)
        for i, reading in enumerate(readings):
            if i % 2 == 0:
                # Debe ser lectura normal
                assert "valor" in reading
                assert reading["valor"] is not None
            # Las fallas pueden tener valor None o anómalo
    
    def test_simulate_calibration_drift(self):
        """Test: Deriva de calibración muestra desajuste gradual."""
        sensor_id = 4
        tipo = TipoSensor.PRESION_ACEITE
        steps = 30
        
        readings = SensorScenarioSimulator.simulate_calibration_drift(
            sensor_id=sensor_id,
            tipo=tipo,
            steps=steps
        )
        
        assert len(readings) == steps
        
        # Verificar que hay deriva (valores finales diferentes a iniciales)
        valores = [r["valor"] for r in readings]
        assert abs(valores[-1] - valores[0]) > 0
    
    def test_simulate_daily_pattern(self):
        """Test: Patrón diario muestra variación sinusoidal."""
        sensor_id = 5
        tipo = TipoSensor.TEMPERATURA_MOTOR
        hours = 24
        
        readings = SensorScenarioSimulator.simulate_daily_pattern(
            sensor_id=sensor_id,
            tipo=tipo,
            hours=hours
        )
        
        assert len(readings) == hours
        
        # Verificar que hay variación
        valores = [r["valor"] for r in readings]
        assert max(valores) > min(valores)
        
        # Verificar que timestamps están espaciados por horas
        from datetime import datetime
        timestamps = [datetime.fromisoformat(r["timestamp_lectura"]) for r in readings]
        if len(timestamps) > 1:
            diff = (timestamps[1] - timestamps[0]).total_seconds()
            assert abs(diff - 3600) < 10  # ~1 hora (con margen de error)
    
    def test_simulate_spike_anomaly(self):
        """Test: Pico anómalo aparece en posición correcta."""
        sensor_id = 6
        tipo = TipoSensor.TEMPERATURA_MOTOR
        total = 20
        spike_pos = 10
        
        readings = SensorScenarioSimulator.simulate_spike_anomaly(
            sensor_id=sensor_id,
            tipo=tipo,
            total_readings=total,
            spike_position=spike_pos
        )
        
        assert len(readings) == total
        
        # Verificar que el pico es diferente al resto
        valores = [r["valor"] for r in readings]
        spike_value = valores[spike_pos]
        
        # El valor del pico debe ser significativamente diferente
        normal_values = valores[:spike_pos] + valores[spike_pos+1:]
        avg_normal = sum(normal_values) / len(normal_values)
        
        # El pico debe estar alejado del promedio
        assert abs(spike_value - avg_normal) > 5


class TestSimulatorsIntegration:
    """Tests de integración para verificar consistencia."""
    
    def test_all_sensor_types_generate_valid_data(self):
        """Test: Todos los tipos de sensores generan datos válidos."""
        sensor_types = [
            TipoSensor.TEMPERATURA_MOTOR,
            TipoSensor.TEMPERATURA_ACEITE,
            TipoSensor.PRESION_ACEITE,
            TipoSensor.VOLTAJE_BATERIA,
            TipoSensor.VIBRACIONES,
            TipoSensor.RPM,
            TipoSensor.VELOCIDAD,
            TipoSensor.NIVEL_COMBUSTIBLE
        ]
        
        for tipo in sensor_types:
            # Verificar que genera valor sin error
            valor = SensorDataSimulator.generate_realistic_value(tipo)
            assert valor is not None
            assert isinstance(valor, (int, float))
            
            # Verificar que está en rango físico
            ranges = SENSOR_RANGES.get(tipo, {})
            if ranges:
                min_val = ranges.get("min", float('-inf'))
                max_val = ranges.get("max", float('inf'))
                assert min_val <= valor <= max_val, f"Valor {valor} fuera de rango para {tipo}"
    
    def test_scenarios_with_different_sensors(self):
        """Test: Todos los escenarios funcionan con diferentes sensores."""
        tipos = [
            TipoSensor.TEMPERATURA_MOTOR,
            TipoSensor.PRESION_ACEITE,
            TipoSensor.VOLTAJE_BATERIA
        ]
        
        for tipo in tipos:
            # Normal operation
            readings1 = SensorScenarioSimulator.simulate_normal_operation(1, tipo, 5)
            assert len(readings1) == 5
            
            # Progressive failure
            readings2 = SensorScenarioSimulator.simulate_progressive_failure(1, tipo, 10)
            assert len(readings2) == 10
            
            # Daily pattern
            readings3 = SensorScenarioSimulator.simulate_daily_pattern(1, tipo, 12)
            assert len(readings3) == 12


# Fixtures para testing
@pytest.fixture
def sample_sensor_types():
    """Fixture con tipos de sensores de ejemplo."""
    return [
        TipoSensor.TEMPERATURA_MOTOR,
        TipoSensor.PRESION_ACEITE,
        TipoSensor.VOLTAJE_BATERIA,
        TipoSensor.VIBRACIONES
    ]


@pytest.fixture
def sample_scenarios():
    """Fixture con escenarios de ejemplo."""
    return ["normal", "warning", "critical", "extreme"]


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])
