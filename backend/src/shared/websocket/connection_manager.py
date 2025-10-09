"""
Connection Manager para WebSocket.
Gestiona conexiones activas, broadcast y mensajes dirigidos.
"""
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Gestor centralizado de conexiones WebSocket.
    
    Maneja:
    - Conexiones por usuario
    - Broadcast a todos los usuarios
    - Mensajes a usuarios específicos
    - Salas/rooms para agrupaciones
    """
    
    def __init__(self):
        # Conexiones activas por usuario: {user_id: [WebSocket, WebSocket, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Conexiones en salas: {room_id: {user_id, user_id, ...}}
        self.rooms: Dict[str, Set[str]] = {}
        
        # Metadata de conexiones: {websocket: {user_id, connected_at, ...}}
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        metadata: Optional[dict] = None
    ):
        """
        Conecta un WebSocket y lo asocia a un usuario.
        
        Args:
            websocket: Instancia de WebSocket
            user_id: ID del usuario
            metadata: Metadata adicional (opcional)
        """
        await websocket.accept()
        
        # Agregar a lista de conexiones del usuario
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Guardar metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            **(metadata or {})
        }
        
        logger.info(
            f"Usuario {user_id} conectado. "
            f"Total conexiones: {len(self.active_connections[user_id])}"
        )
    
    async def disconnect(self, websocket: WebSocket):
        """
        Desconecta un WebSocket y limpia su información.
        
        Args:
            websocket: Instancia de WebSocket a desconectar
        """
        # Obtener user_id antes de eliminar metadata
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        user_id = metadata["user_id"]
        
        # Remover de lista de conexiones del usuario
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Si no quedan conexiones, eliminar entrada
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remover de todas las salas
        for room_users in self.rooms.values():
            room_users.discard(user_id)
        
        # Eliminar metadata
        del self.connection_metadata[websocket]
        
        logger.info(f"Usuario {user_id} desconectado")
    
    async def send_personal_message(
        self,
        message: dict,
        user_id: str
    ):
        """
        Envía un mensaje a todas las conexiones de un usuario específico.
        
        Args:
            message: Diccionario con el mensaje
            user_id: ID del usuario destinatario
        """
        if user_id not in self.active_connections:
            logger.warning(f"Usuario {user_id} no tiene conexiones activas")
            return
        
        # Convertir a JSON
        message_json = json.dumps(message)
        
        # Enviar a todas las conexiones del usuario
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error enviando mensaje a {user_id}: {e}")
                disconnected.append(websocket)
        
        # Limpiar conexiones rotas
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """
        Envía un mensaje a TODOS los usuarios conectados.
        
        Args:
            message: Diccionario con el mensaje
            exclude_user: User ID a excluir del broadcast (opcional)
        """
        message_json = json.dumps(message)
        
        for user_id, connections in list(self.active_connections.items()):
            if exclude_user and user_id == exclude_user:
                continue
            
            disconnected = []
            for websocket in connections:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error en broadcast a {user_id}: {e}")
                    disconnected.append(websocket)
            
            # Limpiar conexiones rotas
            for ws in disconnected:
                await self.disconnect(ws)
    
    async def join_room(self, user_id: str, room_id: str):
        """
        Añade un usuario a una sala.
        
        Args:
            user_id: ID del usuario
            room_id: ID de la sala (ej: "moto_123", "chat_456")
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        logger.info(f"Usuario {user_id} unido a sala {room_id}")
    
    async def leave_room(self, user_id: str, room_id: str):
        """
        Remueve un usuario de una sala.
        
        Args:
            user_id: ID del usuario
            room_id: ID de la sala
        """
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            
            # Si la sala queda vacía, eliminarla
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            
            logger.info(f"Usuario {user_id} salió de sala {room_id}")
    
    async def broadcast_to_room(self, message: dict, room_id: str):
        """
        Envía un mensaje a todos los usuarios en una sala.
        
        Args:
            message: Diccionario con el mensaje
            room_id: ID de la sala
        """
        if room_id not in self.rooms:
            logger.warning(f"Sala {room_id} no existe")
            return
        
        # Enviar a cada usuario en la sala
        for user_id in self.rooms[room_id]:
            await self.send_personal_message(message, user_id)
    
    def get_active_users(self) -> List[str]:
        """Retorna lista de user_ids con conexiones activas."""
        return list(self.active_connections.keys())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Retorna número de conexiones activas de un usuario."""
        return len(self.active_connections.get(user_id, []))
    
    def get_room_users(self, room_id: str) -> Set[str]:
        """Retorna usuarios en una sala."""
        return self.rooms.get(room_id, set())
    
    def is_user_online(self, user_id: str) -> bool:
        """Verifica si un usuario está conectado."""
        return user_id in self.active_connections
    
    def get_total_connections(self) -> int:
        """Retorna número total de conexiones activas."""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del connection manager."""
        return {
            "total_users": len(self.active_connections),
            "total_connections": self.get_total_connections(),
            "total_rooms": len(self.rooms),
            "active_users": self.get_active_users(),
        }


# Instancia global del connection manager
connection_manager = ConnectionManager()
