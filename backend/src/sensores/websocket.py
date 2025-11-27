"""
WebSocket handler para telemetría en tiempo real (MVP).

Arquitectura simplificada sin queue:
- WebSocket directo → CreateLecturaUseCase → DB + Eventos
- Sin worker background (procesamiento síncrono)
- Broadcast de estados actualizados a clientes conectados

Endpoints:
- /ws/sensores/{moto_id}: Canal de telemetría por moto

Mensajes:
- Cliente → Servidor: publish_reading (registrar lectura)
- Servidor → Cliente: reading_ack, component_state_updated, alert

Autenticación: JWT token via query param o header
"""
import logging
import json
from typing import Dict, Set, Optional, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..config.dependencies import get_current_user_ws
from ..shared.exceptions import NotFoundError, ValidationError, UnauthorizedException

from .schemas import CreateLecturaRequest
from .use_cases import CreateLecturaUseCase, UpdateComponentStateUseCase
from .validators import validate_moto_exists

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== CONNECTION MANAGER ====================

class ConnectionManager:
    """
    Gestor de conexiones WebSocket por moto.
    
    Mantiene rooms (moto_id → set de WebSockets) para broadcast.
    """
    
    def __init__(self):
        # {moto_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        logger.info("ConnectionManager inicializado")
    
    async def connect(self, websocket: WebSocket, moto_id: int, user_id: int):
        """Aceptar conexión y agregar a room."""
        await websocket.accept()
        
        if moto_id not in self.active_connections:
            self.active_connections[moto_id] = set()
        
        self.active_connections[moto_id].add(websocket)
        
        logger.info(
            f"WebSocket conectado: moto_id={moto_id}, user_id={user_id}, "
            f"total_connections={len(self.active_connections[moto_id])}"
        )
        
        # Enviar mensaje de bienvenida
        await self.send_personal_message({
            "type": "connection_ack",
            "message": f"Conectado a telemetría de moto {moto_id}",
            "moto_id": moto_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, moto_id: int):
        """Remover conexión de room."""
        if moto_id in self.active_connections:
            self.active_connections[moto_id].discard(websocket)
            
            # Limpiar room vacío
            if not self.active_connections[moto_id]:
                del self.active_connections[moto_id]
            
            logger.info(
                f"WebSocket desconectado: moto_id={moto_id}, "
                f"remaining={len(self.active_connections.get(moto_id, []))}"
            )
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Enviar mensaje a un WebSocket específico."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error enviando mensaje personal: {e}")
    
    async def broadcast_to_moto(self, message: Dict[str, Any], moto_id: int):
        """Broadcast a todos los clientes conectados a una moto."""
        if moto_id not in self.active_connections:
            logger.debug(f"No hay conexiones para moto {moto_id}")
            return
        
        # Copiar set para evitar modificación durante iteración
        connections = self.active_connections[moto_id].copy()
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error en broadcast a moto {moto_id}: {e}")
                # Remover conexión muerta
                self.disconnect(websocket, moto_id)


# Singleton global
manager = ConnectionManager()


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws/sensores/{moto_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    moto_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket para telemetría en tiempo real.
    
    Autenticación:
    - Token JWT via query param: /ws/sensores/{moto_id}?token=xxx
    
    Mensajes del cliente:
    {
        "type": "publish_reading",
        "sensor_id": "uuid",
        "ts": "ISO8601",
        "valor": {"value": X, "unit": "Y"},
        "metadata": {}
    }
    
    Mensajes del servidor:
    - connection_ack: Confirmación de conexión
    - reading_ack: Lectura recibida y procesada
    - component_state_updated: Estado de componente cambió
    - alert: Alerta por umbral violado
    - error: Error en procesamiento
    """
    current_user = None
    
    try:
        # Autenticación
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Validar token y obtener usuario
        try:
            current_user = await get_current_user_ws(token, db)
            logger.info(f"Autenticación WS exitosa: user_id={current_user.id}")
        except UnauthorizedException as e:
            logger.warning(f"Autenticación WS fallida: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Validar moto existe
        try:
            await validate_moto_exists(db, moto_id)
        except NotFoundError:
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
            return
        
        # TODO: Validar que current_user sea propietario de la moto
        
        # Conectar
        await manager.connect(websocket, moto_id, current_user.id)
        
        # Loop de mensajes
        while True:
            try:
                # Recibir mensaje
                data = await websocket.receive_json()
                
                message_type = data.get("type")
                logger.debug(f"Mensaje recibido: type={message_type}, moto_id={moto_id}")
                
                if message_type == "publish_reading":
                    await handle_publish_reading(
                        data=data,
                        moto_id=moto_id,
                        websocket=websocket,
                        db=db
                    )
                
                elif message_type == "ping":
                    # Heartbeat
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()},
                        websocket
                    )
                
                else:
                    logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Tipo de mensaje desconocido: {message_type}"
                    }, websocket)
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON inválido: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "JSON inválido"
                }, websocket)
            
            except WebSocketDisconnect:
                logger.info(f"Cliente desconectado: moto_id={moto_id}")
                break
                
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    
    finally:
        # Cleanup
        if current_user:
            manager.disconnect(websocket, moto_id)


# ==================== MESSAGE HANDLERS ====================

async def handle_publish_reading(
    data: Dict[str, Any],
    moto_id: int,
    websocket: WebSocket,
    db: AsyncSession
):
    """
    Procesar lectura de sensor.
    
    Flujo:
    1. Validar datos
    2. Crear lectura (use case)
    3. Commit DB
    4. Enviar ACK al cliente
    5. Broadcast estado actualizado a room (opcional)
    """
    try:
        # 1. Validar datos
        sensor_id_str = data.get("sensor_id")
        if not sensor_id_str:
            raise ValidationError("sensor_id es requerido")
        
        sensor_id = UUID(sensor_id_str)
        
        # 2. Crear request schema
        lectura_request = CreateLecturaRequest(
            sensor_id=sensor_id,
            ts=datetime.fromisoformat(data["ts"]) if "ts" in data else datetime.now(timezone.utc),
            valor=data.get("valor", {}),
            metadata=data.get("metadata")
        )
        
        # 3. Ejecutar use case
        use_case = CreateLecturaUseCase(db)
        lectura = await use_case.execute(lectura_request)
        
        # 4. Commit
        await db.commit()
        
        logger.info(f"Lectura registrada via WS: id={lectura.id}, sensor_id={sensor_id}")
        
        # 5. Enviar ACK al cliente
        await manager.send_personal_message({
            "type": "reading_ack",
            "lectura_id": lectura.id,
            "sensor_id": str(lectura.sensor_id),
            "timestamp": lectura.ts.isoformat(),
            "message": "Lectura registrada exitosamente"
        }, websocket)
        
        # 6. Si la lectura tiene componente, actualizar estado y broadcast
        if lectura.componente_id:
            try:
                update_use_case = UpdateComponentStateUseCase(db)
                state_response = await update_use_case.execute(
                    componente_id=lectura.componente_id,
                    moto_id=lectura.moto_id
                )
                await db.commit()
                
                # Broadcast estado actualizado (siempre, no hay campo 'changed')
                await manager.broadcast_to_moto({
                    "type": "component_state_updated",
                    "componente_id": state_response.componente_id,
                    "moto_id": state_response.moto_id,
                    "tipo": state_response.tipo,
                    "component_state": state_response.component_state.value,
                    "sensor_count": state_response.sensor_count,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, moto_id)
                
                logger.info(
                    f"Estado de componente actualizado y broadcasted: "
                    f"componente_id={state_response.componente_id}, state={state_response.component_state.value}"
                )
            except Exception as e:
                logger.error(f"Error actualizando estado de componente: {e}")
                # No fallar la lectura por esto
        
    except ValidationError as e:
        logger.warning(f"Validación fallida en publish_reading: {e}")
        await manager.send_personal_message({
            "type": "error",
            "error_type": "validation_error",
            "message": str(e)
        }, websocket)
        await db.rollback()
        
    except NotFoundError as e:
        logger.warning(f"Recurso no encontrado: {e}")
        await manager.send_personal_message({
            "type": "error",
            "error_type": "not_found",
            "message": str(e)
        }, websocket)
        await db.rollback()
        
    except Exception as e:
        logger.error(f"Error procesando lectura: {e}")
        await manager.send_personal_message({
            "type": "error",
            "error_type": "internal_error",
            "message": "Error interno al procesar lectura"
        }, websocket)
        await db.rollback()


# ==================== UTILITY ====================

async def broadcast_alert_to_moto(moto_id: int, alert_data: Dict[str, Any]):
    """
    Función helper para broadcast de alertas desde otros módulos.
    
    Uso: Llamar desde event listeners cuando se emita AlertaSensorEvent.
    """
    await manager.broadcast_to_moto({
        "type": "alert",
        **alert_data
    }, moto_id)
