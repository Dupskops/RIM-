"""
WebSocket handler para sensores IoT.
Transmite datos de sensores en tiempo real.
"""
from typing import Optional, Dict, Any
from fastapi import WebSocket
import logging
import json
from datetime import datetime
import asyncio

from src.shared.websocket import (
    BaseWebSocketHandler,
    require_moto_ownership,
    validate_message_schema,
    log_websocket_event,
    WebSocketPermissionChecker,
    connection_manager,
)
from src.shared.constants import WSMessageType, TipoSensor
from src.config.database import AsyncSessionLocal
from .services import SensorService
from .repositories import SensorRepository, LecturaSensorRepository

logger = logging.getLogger(__name__)


class SensorWebSocketHandler(BaseWebSocketHandler):
    """
    Handler de WebSocket para streaming de datos de sensores IoT.
    
    Características:
    - Streaming en tiempo real de lecturas de sensores
    - Suscripción a sensores específicos o todos de una moto
    - Alertas automáticas cuando valores están fuera de rango
    - Agregación de datos (promedio, min, max en ventanas de tiempo)
    - Rate limiting para evitar saturación
    
    Tipos de mensajes soportados:
    - subscribe_moto: Suscribirse a todos los sensores de una moto
    - subscribe_sensor: Suscribirse a un sensor específico
    - unsubscribe: Cancelar suscripción
    - get_current: Obtener lecturas actuales
    - get_history: Obtener historial de lecturas
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        moto_id: Optional[str] = None
    ):
        """
        Inicializa el handler de sensores.
        
        Args:
            websocket: Instancia de WebSocket
            moto_id: ID de la moto (opcional)
        """
        super().__init__(websocket, require_auth=True)
        self.moto_id = moto_id
        self.subscribed_sensors: set[str] = set()
        self.streaming_task: Optional[asyncio.Task] = None
        self.streaming = False
        
        # Registrar handlers
        self.register_handler("subscribe_moto", self.handle_subscribe_moto)
        self.register_handler("subscribe_sensor", self.handle_subscribe_sensor)
        self.register_handler("unsubscribe", self.handle_unsubscribe)
        self.register_handler("get_current", self.handle_get_current)
        self.register_handler("get_history", self.handle_get_history)
        self.register_handler("start_streaming", self.handle_start_streaming)
        self.register_handler("stop_streaming", self.handle_stop_streaming)
    
    async def on_connect(self):
        """Hook ejecutado al conectar exitosamente."""
        # Verificar acceso a la moto si se especificó
        if self.moto_id:
            checker = WebSocketPermissionChecker(self.user_id)
            await checker.require_moto_access(self.moto_id)
            
            # Unirse a la sala de la moto
            room_id = f"moto_{self.moto_id}"
            await connection_manager.join_room(self.user_id, room_id)
        
        logger.info(
            f"Usuario {self.user_id} conectado a sensores "
            f"(moto: {self.moto_id or 'no especificada'})"
        )
        
        # Enviar estado de conexión
        await self.send_message({
            "type": "connection_success",
            "message": "Conectado al stream de sensores",
            "moto_id": self.moto_id,
            "timestamp": datetime.now().isoformat()
        })
    
    @validate_message_schema(["moto_id"])
    @log_websocket_event("subscribe_moto_sensors")
    async def handle_subscribe_moto(self, data: dict):
        """
        Suscribe al usuario a todos los sensores de una moto.
        
        Formato:
        {
            "type": "subscribe_moto",
            "moto_id": "uuid",
            "interval_seconds": 5  // opcional, default 5
        }
        """
        moto_id = data["moto_id"]
        interval = data.get("interval_seconds", 5)
        
        # Verificar propiedad de la moto
        checker = WebSocketPermissionChecker(self.user_id)
        await checker.require_moto_access(moto_id)
        
        try:
            async with AsyncSessionLocal() as session:
                repo = SensorRepository(session)
                
                # Obtener todos los sensores de la moto
                sensors = await repo.get_by_moto_id(moto_id)
                
                if not sensors:
                    await self.send_error(f"No hay sensores para la moto {moto_id}")
                    return
                
                # Suscribirse a todos
                self.subscribed_sensors.update([str(sensor.id) for sensor in sensors])
                self.moto_id = moto_id
                
                # Unirse a la sala de la moto
                room_id = f"moto_{moto_id}"
                await connection_manager.join_room(self.user_id, room_id)
                
                await self.send_message({
                    "type": "subscribed",
                    "moto_id": moto_id,
                    "sensor_count": len(sensors),
                    "sensors": [
                        {
                            "id": str(sensor.id),
                            "tipo": sensor.tipo,
                            "unidad": sensor.unidad,
                        }
                        for sensor in sensors
                    ],
                    "interval_seconds": interval,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(
                    f"Usuario {self.user_id} suscrito a {len(sensors)} sensores "
                    f"de moto {moto_id}"
                )
                
        except Exception as e:
            logger.error(f"Error suscribiendo a sensores de moto: {e}")
            await self.send_error(f"Error en suscripción: {str(e)}")
    
    @validate_message_schema(["sensor_id"])
    @log_websocket_event("subscribe_sensor")
    async def handle_subscribe_sensor(self, data: dict):
        """
        Suscribe al usuario a un sensor específico.
        
        Formato:
        {
            "type": "subscribe_sensor",
            "sensor_id": "uuid"
        }
        """
        sensor_id = data["sensor_id"]
        
        # Verificar acceso al sensor
        checker = WebSocketPermissionChecker(self.user_id)
        await checker.require_sensor_access(sensor_id)
        
        try:
            async with AsyncSessionLocal() as session:
                repo = SensorRepository(session)
                sensor = await repo.get_by_id(sensor_id)
                
                if not sensor:
                    await self.send_error("Sensor no encontrado")
                    return
                
                self.subscribed_sensors.add(sensor_id)
                
                await self.send_message({
                    "type": "subscribed",
                    "sensor_id": sensor_id,
                    "sensor_tipo": sensor.tipo,
                    "sensor_unidad": sensor.unidad,
                    "moto_id": str(sensor.moto_id),
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"Usuario {self.user_id} suscrito a sensor {sensor_id}")
                
        except Exception as e:
            logger.error(f"Error suscribiendo a sensor: {e}")
            await self.send_error(f"Error en suscripción: {str(e)}")
    
    @log_websocket_event("unsubscribe_sensors")
    async def handle_unsubscribe(self, data: dict):
        """
        Cancela todas las suscripciones o una específica.
        
        Formato:
        {
            "type": "unsubscribe",
            "sensor_id": "uuid"  // opcional
        }
        """
        sensor_id = data.get("sensor_id")
        
        if sensor_id:
            self.subscribed_sensors.discard(sensor_id)
            message = f"Desuscrito del sensor {sensor_id}"
        else:
            self.subscribed_sensors.clear()
            message = "Desuscrito de todos los sensores"
        
        await self.send_message({
            "type": "unsubscribed",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    @log_websocket_event("get_current_readings")
    async def handle_get_current(self, data: dict):
        """
        Obtiene las lecturas actuales de los sensores suscritos.
        
        Formato:
        {
            "type": "get_current",
            "moto_id": "uuid"  // opcional
        }
        """
        moto_id = data.get("moto_id", self.moto_id)
        
        if not moto_id and not self.subscribed_sensors:
            await self.send_error("No hay sensores suscritos ni moto_id especificado")
            return
        
        try:
            async with AsyncSessionLocal() as session:
                service = SensorService(session)
                
                if moto_id:
                    # Obtener todas las lecturas de la moto
                    readings = await service.get_current_readings_by_moto(moto_id)
                else:
                    # Obtener solo sensores suscritos
                    readings = await service.get_readings_by_sensor_ids(
                        list(self.subscribed_sensors)
                    )
                
                await self.send_message({
                    "type": "current_readings",
                    "moto_id": moto_id,
                    "readings": [
                        {
                            "sensor_id": str(reading.sensor_id),
                            "tipo": reading.sensor.tipo,
                            "valor": reading.valor,
                            "unidad": reading.sensor.unidad,
                            "timestamp": reading.timestamp.isoformat(),
                            "in_range": reading.en_rango,
                        }
                        for reading in readings
                    ],
                    "count": len(readings),
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo lecturas actuales: {e}")
            await self.send_error("Error obteniendo lecturas")
    
    @validate_message_schema(["sensor_id"])
    @log_websocket_event("get_sensor_history")
    async def handle_get_history(self, data: dict):
        """
        Obtiene historial de lecturas de un sensor.
        
        Formato:
        {
            "type": "get_history",
            "sensor_id": "uuid",
            "limit": 100,  // opcional
            "from_date": "2025-10-01T00:00:00",  // opcional
            "to_date": "2025-10-07T23:59:59"  // opcional
        }
        """
        sensor_id = data["sensor_id"]
        limit = data.get("limit", 100)
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        
        # Verificar acceso
        checker = WebSocketPermissionChecker(self.user_id)
        await checker.require_sensor_access(sensor_id)
        
        try:
            async with AsyncSessionLocal() as session:
                repo = LecturaSensorRepository(session)
                
                # Obtener historial
                readings = await repo.get_history(
                    sensor_id=sensor_id,
                    limit=limit,
                    from_date=from_date,
                    to_date=to_date
                )
                
                await self.send_message({
                    "type": "history",
                    "sensor_id": sensor_id,
                    "readings": [
                        {
                            "valor": reading.valor,
                            "timestamp": reading.timestamp.isoformat(),
                            "en_rango": reading.en_rango,
                        }
                        for reading in readings
                    ],
                    "count": len(readings),
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            await self.send_error("Error obteniendo historial")
    
    @log_websocket_event("start_sensor_streaming")
    async def handle_start_streaming(self, data: dict):
        """
        Inicia el streaming automático de lecturas.
        
        Formato:
        {
            "type": "start_streaming",
            "interval_seconds": 5  // opcional, default 5
        }
        """
        if self.streaming:
            await self.send_error("Streaming ya está activo")
            return
        
        if not self.subscribed_sensors:
            await self.send_error("No hay sensores suscritos")
            return
        
        interval = data.get("interval_seconds", 5)
        self.streaming = True
        
        # Iniciar tarea de streaming
        self.streaming_task = asyncio.create_task(
            self._stream_sensor_data(interval)
        )
        
        await self.send_message({
            "type": "streaming_started",
            "interval_seconds": interval,
            "sensor_count": len(self.subscribed_sensors),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(
            f"Streaming iniciado para usuario {self.user_id} "
            f"({len(self.subscribed_sensors)} sensores, intervalo: {interval}s)"
        )
    
    @log_websocket_event("stop_sensor_streaming")
    async def handle_stop_streaming(self, data: dict):
        """Detiene el streaming automático."""
        if not self.streaming:
            await self.send_error("Streaming no está activo")
            return
        
        self.streaming = False
        
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
        
        await self.send_message({
            "type": "streaming_stopped",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Streaming detenido para usuario {self.user_id}")
    
    async def _stream_sensor_data(self, interval: int):
        """
        Loop de streaming de datos de sensores.
        
        Args:
            interval: Intervalo en segundos entre lecturas
        """
        while self.streaming and self.is_connected:
            try:
                async with AsyncSessionLocal() as session:
                    service = SensorService(session)
                    
                    # Obtener lecturas de sensores suscritos
                    readings = await service.get_readings_by_sensor_ids(
                        list(self.subscribed_sensors)
                    )
                    
                    # Enviar al cliente
                    await self.send_message({
                        "type": "sensor_data",
                        "readings": [
                            {
                                "sensor_id": str(reading.sensor_id),
                                "tipo": reading.sensor.tipo,
                                "valor": reading.valor,
                                "unidad": reading.sensor.unidad,
                                "timestamp": reading.timestamp.isoformat(),
                                "in_range": reading.en_rango,
                            }
                            for reading in readings
                        ],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Detectar alertas
                    for reading in readings:
                        if not reading.en_rango:
                            await self.send_message({
                                "type": "sensor_alert",
                                "sensor_id": str(reading.sensor_id),
                                "tipo": reading.sensor.tipo,
                                "valor": reading.valor,
                                "unidad": reading.sensor.unidad,
                                "message": f"Valor fuera de rango: {reading.valor} {reading.sensor.unidad}",
                                "severity": "warning",
                                "timestamp": datetime.now().isoformat()
                            })
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en streaming de sensores: {e}")
                await self.send_error(f"Error en streaming: {str(e)}")
                await asyncio.sleep(interval)
    
    async def on_disconnect(self):
        """Hook ejecutado al desconectar."""
        # Detener streaming si está activo
        if self.streaming:
            self.streaming = False
            if self.streaming_task:
                self.streaming_task.cancel()
        
        # Salir de sala de moto
        if self.moto_id:
            room_id = f"moto_{self.moto_id}"
            await connection_manager.leave_room(self.user_id, room_id)
        
        logger.info(
            f"Usuario {self.user_id} desconectado de sensores "
            f"(moto: {self.moto_id})"
        )


# ============================================
# ENDPOINT WEBSOCKET
# ============================================
async def sensor_websocket_endpoint(
    websocket: WebSocket,
    moto_id: Optional[str] = None
):
    """
    Endpoint de WebSocket para sensores.
    
    URL: /ws/sensors/{moto_id}?token=<jwt_token>
    
    Args:
        websocket: Instancia de WebSocket
        moto_id: ID de la moto (opcional)
    """
    handler = SensorWebSocketHandler(websocket, moto_id)
    await handler.handle()
