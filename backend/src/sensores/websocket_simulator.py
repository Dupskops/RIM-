"""
WebSocket handler para streaming de datos simulados en tiempo real.
Útil para demos, testing y desarrollo sin hardware real.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import WebSocket
from datetime import datetime

from src.shared.websocket import (
    BaseWebSocketHandler,
    validate_message_schema,
    log_websocket_event,
)
from src.shared.constants import TipoSensor
from src.sensores.simulators import SensorDataSimulator, SensorScenarioSimulator

logger = logging.getLogger(__name__)


class SimulatedSensorWebSocketHandler(BaseWebSocketHandler):
    """
    Handler de WebSocket para streaming de datos simulados.
    
    Permite simular múltiples sensores transmitiendo datos en tiempo real
    sin necesidad de hardware IoT físico.
    
    Tipos de mensajes soportados:
    - start_simulation: Iniciar simulación de un sensor
    - start_scenario: Iniciar escenario específico (normal, failure, etc.)
    - stop_simulation: Detener simulación
    - change_scenario: Cambiar escenario en vivo
    - get_simulation_status: Estado actual de simulaciones
    """
    
    def __init__(self, websocket: WebSocket):
        """
        Inicializa el handler de simulación.
        
        Args:
            websocket: Instancia de WebSocket
        """
        super().__init__(websocket, require_auth=False)  # Demo mode, no auth
        self.simulations: Dict[int, Dict[str, Any]] = {}  # {sensor_id: config}
        self.simulation_tasks: Dict[int, asyncio.Task] = {}
        
        # Registrar handlers
        self.register_handler("start_simulation", self.handle_start_simulation)
        self.register_handler("start_scenario", self.handle_start_scenario)
        self.register_handler("stop_simulation", self.handle_stop_simulation)
        self.register_handler("stop_all", self.handle_stop_all)
        self.register_handler("change_scenario", self.handle_change_scenario)
        self.register_handler("get_status", self.handle_get_status)
    
    async def on_connect(self):
        """Hook ejecutado al conectar."""
        logger.info("Cliente conectado al simulador de sensores")
        
        await self.send_message({
            "type": "connection",
            "status": "connected",
            "message": "Simulador de sensores IoT listo",
            "available_sensors": [tipo.value for tipo in TipoSensor],
            "scenarios": ["normal", "warning", "critical", "extreme", 
                         "progressive_failure", "intermittent", "daily_pattern"]
        })
    
    @validate_message_schema(["sensor_id", "tipo", "interval"])
    @log_websocket_event("start_simulation")
    async def handle_start_simulation(self, data: dict):
        """
        Inicia simulación de un sensor.
        
        Payload esperado:
        {
            "action": "start_simulation",
            "sensor_id": 1,
            "tipo": "temperatura_motor",
            "interval": 2,  // segundos entre lecturas
            "scenario": "normal"  // opcional
        }
        """
        sensor_id = data["sensor_id"]
        tipo_str = data["tipo"]
        interval = data.get("interval", 2)
        scenario = data.get("scenario", "normal")
        
        # Validar tipo de sensor
        try:
            tipo = TipoSensor(tipo_str)
        except ValueError:
            await self.send_message({
                "type": "error",
                "message": f"Tipo de sensor inválido: {tipo_str}"
            })
            return
        
        # Detener simulación existente si hay
        if sensor_id in self.simulation_tasks:
            await self.stop_simulation(sensor_id)
        
        # Configurar simulación
        self.simulations[sensor_id] = {
            "tipo": tipo,
            "interval": interval,
            "scenario": scenario,
            "started_at": datetime.now().isoformat(),
            "readings_sent": 0
        }
        
        # Iniciar tarea de simulación
        task = asyncio.create_task(
            self._simulate_sensor(sensor_id, tipo, interval, scenario)
        )
        self.simulation_tasks[sensor_id] = task
        
        await self.send_message({
            "type": "simulation_started",
            "sensor_id": sensor_id,
            "tipo": tipo.value,
            "interval": interval,
            "scenario": scenario,
            "message": f"Simulación iniciada para sensor {sensor_id}"
        })
    
    @validate_message_schema(["sensor_id", "scenario_type"])
    @log_websocket_event("start_scenario")
    async def handle_start_scenario(self, data: dict):
        """
        Inicia un escenario completo predefinido.
        
        Payload esperado:
        {
            "action": "start_scenario",
            "sensor_id": 1,
            "tipo": "temperatura_motor",
            "scenario_type": "progressive_failure",
            "duration": 60  // segundos totales
        }
        """
        sensor_id = data["sensor_id"]
        tipo_str = data["tipo"]
        scenario_type = data["scenario_type"]
        duration = data.get("duration", 60)
        
        try:
            tipo = TipoSensor(tipo_str)
        except ValueError:
            await self.send_message({
                "type": "error",
                "message": f"Tipo de sensor inválido: {tipo_str}"
            })
            return
        
        # Generar datos del escenario
        readings = []
        
        if scenario_type == "progressive_failure":
            readings = SensorScenarioSimulator.simulate_progressive_failure(
                sensor_id=sensor_id,
                tipo=tipo,
                steps=duration
            )
        elif scenario_type == "intermittent":
            readings = SensorScenarioSimulator.simulate_intermittent_failure(
                sensor_id=sensor_id,
                tipo=tipo,
                cycles=duration
            )
        elif scenario_type == "daily_pattern":
            readings = SensorScenarioSimulator.simulate_daily_pattern(
                sensor_id=sensor_id,
                tipo=tipo,
                hours=min(duration, 24)
            )
        elif scenario_type == "calibration_drift":
            readings = SensorScenarioSimulator.simulate_calibration_drift(
                sensor_id=sensor_id,
                tipo=tipo,
                steps=duration
            )
        elif scenario_type == "spike_anomaly":
            readings = SensorScenarioSimulator.simulate_spike_anomaly(
                sensor_id=sensor_id,
                tipo=tipo,
                total_readings=duration,
                spike_position=duration // 2
            )
        else:
            await self.send_message({
                "type": "error",
                "message": f"Escenario no reconocido: {scenario_type}"
            })
            return
        
        # Enviar escenario completo
        task = asyncio.create_task(
            self._stream_scenario(sensor_id, readings, interval=1)
        )
        self.simulation_tasks[sensor_id] = task
        
        await self.send_message({
            "type": "scenario_started",
            "sensor_id": sensor_id,
            "scenario_type": scenario_type,
            "total_readings": len(readings),
            "message": f"Escenario '{scenario_type}' iniciado"
        })
    
    @validate_message_schema(["sensor_id"])
    @log_websocket_event("stop_simulation")
    async def handle_stop_simulation(self, data: dict):
        """Detiene simulación de un sensor específico."""
        sensor_id = data["sensor_id"]
        
        if await self.stop_simulation(sensor_id):
            await self.send_message({
                "type": "simulation_stopped",
                "sensor_id": sensor_id,
                "message": f"Simulación detenida para sensor {sensor_id}"
            })
        else:
            await self.send_message({
                "type": "error",
                "message": f"No hay simulación activa para sensor {sensor_id}"
            })
    
    @log_websocket_event("stop_all")
    async def handle_stop_all(self, data: dict):
        """Detiene todas las simulaciones activas."""
        stopped_count = 0
        
        for sensor_id in list(self.simulation_tasks.keys()):
            if await self.stop_simulation(sensor_id):
                stopped_count += 1
        
        await self.send_message({
            "type": "all_stopped",
            "stopped_count": stopped_count,
            "message": f"Se detuvieron {stopped_count} simulaciones"
        })
    
    @validate_message_schema(["sensor_id", "scenario"])
    @log_websocket_event("change_scenario")
    async def handle_change_scenario(self, data: dict):
        """Cambia el escenario de una simulación activa."""
        sensor_id = data["sensor_id"]
        new_scenario = data["scenario"]
        
        if sensor_id not in self.simulations:
            await self.send_message({
                "type": "error",
                "message": f"Sensor {sensor_id} no está siendo simulado"
            })
            return
        
        # Actualizar escenario
        self.simulations[sensor_id]["scenario"] = new_scenario
        
        await self.send_message({
            "type": "scenario_changed",
            "sensor_id": sensor_id,
            "new_scenario": new_scenario,
            "message": f"Escenario cambiado a '{new_scenario}'"
        })
    
    @log_websocket_event("get_status")
    async def handle_get_status(self, data: dict):
        """Obtiene estado actual de todas las simulaciones."""
        simulations_status = []
        
        for sensor_id, config in self.simulations.items():
            is_active = sensor_id in self.simulation_tasks
            simulations_status.append({
                "sensor_id": sensor_id,
                "tipo": config["tipo"].value,
                "scenario": config["scenario"],
                "interval": config["interval"],
                "active": is_active,
                "started_at": config["started_at"],
                "readings_sent": config["readings_sent"]
            })
        
        await self.send_message({
            "type": "status",
            "active_simulations": len(self.simulation_tasks),
            "simulations": simulations_status
        })
    
    async def stop_simulation(self, sensor_id: int) -> bool:
        """
        Detiene una simulación específica.
        
        Args:
            sensor_id: ID del sensor
        
        Returns:
            True si se detuvo, False si no existía
        """
        if sensor_id in self.simulation_tasks:
            task = self.simulation_tasks[sensor_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.simulation_tasks[sensor_id]
            if sensor_id in self.simulations:
                del self.simulations[sensor_id]
            
            return True
        
        return False
    
    async def _simulate_sensor(
        self,
        sensor_id: int,
        tipo: TipoSensor,
        interval: float,
        scenario: str
    ):
        """
        Loop de simulación continua para un sensor.
        
        Args:
            sensor_id: ID del sensor
            tipo: Tipo de sensor
            interval: Intervalo en segundos
            scenario: Escenario a simular
        """
        try:
            while True:
                # Generar lectura
                reading = SensorDataSimulator.simulate_sensor_reading(
                    sensor_id=sensor_id,
                    tipo=tipo,
                    scenario=scenario
                )
                
                # Enviar por WebSocket
                await self.send_message({
                    "type": "sensor_reading",
                    "sensor_id": sensor_id,
                    "tipo": tipo.value,
                    "valor": reading["valor"],
                    "timestamp_lectura": reading["timestamp_lectura"],
                    "metadata": reading["metadata_json"],
                    "scenario": scenario
                })
                
                # Actualizar contador
                if sensor_id in self.simulations:
                    self.simulations[sensor_id]["readings_sent"] += 1
                
                # Esperar intervalo
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info(f"Simulación cancelada para sensor {sensor_id}")
        except Exception as e:
            logger.error(f"Error en simulación de sensor {sensor_id}: {e}")
            await self.send_message({
                "type": "error",
                "sensor_id": sensor_id,
                "message": f"Error en simulación: {str(e)}"
            })
    
    async def _stream_scenario(
        self,
        sensor_id: int,
        readings: list,
        interval: float = 1
    ):
        """
        Transmite un escenario completo predefinido.
        
        Args:
            sensor_id: ID del sensor
            readings: Lista de lecturas a transmitir
            interval: Intervalo entre lecturas
        """
        try:
            for idx, reading in enumerate(readings):
                await self.send_message({
                    "type": "scenario_reading",
                    "sensor_id": sensor_id,
                    "reading_index": idx + 1,
                    "total_readings": len(readings),
                    "progress": ((idx + 1) / len(readings)) * 100,
                    "valor": reading["valor"],
                    "timestamp_lectura": reading["timestamp_lectura"],
                    "metadata": reading.get("metadata_json", {})
                })
                
                await asyncio.sleep(interval)
            
            # Escenario completado
            await self.send_message({
                "type": "scenario_completed",
                "sensor_id": sensor_id,
                "total_readings": len(readings),
                "message": "Escenario completado exitosamente"
            })
            
        except asyncio.CancelledError:
            logger.info(f"Escenario cancelado para sensor {sensor_id}")
        except Exception as e:
            logger.error(f"Error transmitiendo escenario: {e}")
    
    async def on_disconnect(self):
        """Hook ejecutado al desconectar."""
        # Detener todas las simulaciones
        for sensor_id in list(self.simulation_tasks.keys()):
            await self.stop_simulation(sensor_id)
        
        logger.info("Cliente desconectado del simulador")


# ============================================
# ENDPOINT WEBSOCKET
# ============================================
async def simulated_sensor_websocket_endpoint(websocket: WebSocket):
    """
    Endpoint de WebSocket para sensores simulados.
    
    URL: /ws/sensors/simulator
    
    No requiere autenticación (modo demo).
    
    Args:
        websocket: Instancia de WebSocket
    """
    handler = SimulatedSensorWebSocketHandler(websocket)
    await handler.handle()
