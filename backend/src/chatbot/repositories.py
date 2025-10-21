"""
Repositorio para operaciones de base de datos del chatbot.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.models import Conversacion, Mensaje


class ConversacionRepository:
    """Repositorio para gestión de conversaciones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversacion: Conversacion) -> Conversacion:
        """Crea una nueva conversación."""
        self.db.add(conversacion)
        await self.db.commit()
        await self.db.refresh(conversacion)
        return conversacion

    async def get_by_id(self, conversacion_id: int) -> Optional[Conversacion]:
        """Obtiene una conversación por ID numérico."""
        result = await self.db.execute(
            select(Conversacion)
            .where(
                and_(
                    Conversacion.id == conversacion_id,
                    Conversacion.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_conversation_id(self, conversation_id: str) -> Optional[Conversacion]:
        """Obtiene una conversación por su conversation_id."""
        result = await self.db.execute(
            select(Conversacion)
            .where(
                and_(
                    Conversacion.conversation_id == conversation_id,
                    Conversacion.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_usuario(
        self,
        usuario_id: int,
        skip: int = 0,
        limit: int = 50,
        solo_activas: bool = False
    ) -> List[Conversacion]:
        """Obtiene conversaciones de un usuario."""
        query = select(Conversacion).where(
            and_(
                Conversacion.usuario_id == usuario_id,
                Conversacion.deleted_at.is_(None)
            )
        )
        
        if solo_activas:
            query = query.where(Conversacion.activa == True)
        
        query = query.order_by(desc(Conversacion.ultima_actividad))
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_activas(self, skip: int = 0, limit: int = 100) -> List[Conversacion]:
        """Obtiene conversaciones activas."""
        result = await self.db.execute(
            select(Conversacion)
            .where(
                and_(
                    Conversacion.activa == True,
                    Conversacion.deleted_at.is_(None)
                )
            )
            .order_by(desc(Conversacion.ultima_actividad))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_usuario(self, usuario_id: int, solo_activas: bool = False) -> int:
        """Cuenta conversaciones de un usuario."""
        query = select(func.count(Conversacion.id)).where(
            and_(
                Conversacion.usuario_id == usuario_id,
                Conversacion.deleted_at.is_(None)
            )
        )
        
        if solo_activas:
            query = query.where(Conversacion.activa == True)
        
        result = await self.db.execute(query)
        return result.scalar_one()

    async def update(self, conversacion: Conversacion) -> Conversacion:
        """Actualiza una conversación."""
        await self.db.commit()
        await self.db.refresh(conversacion)
        return conversacion

    async def actualizar_actividad(self, conversacion: Conversacion) -> None:
        """Actualiza la última actividad de una conversación."""
        conversacion.ultima_actividad = datetime.utcnow()
        conversacion.total_mensajes += 1
        await self.db.commit()

    async def marcar_inactiva(self, conversacion: Conversacion) -> None:
        """Marca una conversación como inactiva."""
        conversacion.activa = False
        await self.db.commit()

    async def delete(self, conversacion: Conversacion) -> None:
        """Soft delete de una conversación."""
        conversacion.deleted_at = datetime.utcnow()
        await self.db.commit()


class MensajeRepository:
    """Repositorio para gestión de mensajes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, mensaje: Mensaje) -> Mensaje:
        """Crea un nuevo mensaje."""
        self.db.add(mensaje)
        await self.db.commit()
        await self.db.refresh(mensaje)
        return mensaje

    async def get_by_id(self, mensaje_id: int) -> Optional[Mensaje]:
        """Obtiene un mensaje por ID."""
        result = await self.db.execute(
            select(Mensaje)
            .where(
                and_(
                    Mensaje.id == mensaje_id,
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_conversacion(
        self,
        conversacion_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mensaje]:
        """Obtiene mensajes de una conversación."""
        result = await self.db.execute(
            select(Mensaje)
            .where(
                and_(
                    Mensaje.conversacion_id == conversacion_id,
                    Mensaje.deleted_at.is_(None)
                )
            )
            .order_by(Mensaje.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ultimos_mensajes(
        self,
        conversacion_id: int,
        limit: int = 10
    ) -> List[Mensaje]:
        """Obtiene los últimos N mensajes de una conversación."""
        result = await self.db.execute(
            select(Mensaje)
            .where(
                and_(
                    Mensaje.conversacion_id == conversacion_id,
                    Mensaje.deleted_at.is_(None)
                )
            )
            .order_by(desc(Mensaje.created_at))
            .limit(limit)
        )
        mensajes = list(result.scalars().all())
        return list(reversed(mensajes))  # Invertir para orden cronológico

    async def count_by_conversacion(self, conversacion_id: int) -> int:
        """Cuenta mensajes de una conversación."""
        result = await self.db.execute(
            select(func.count(Mensaje.id))
            .where(
                and_(
                    Mensaje.conversacion_id == conversacion_id,
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def count_by_usuario_hoy(self, usuario_id: int) -> int:
        """Cuenta mensajes enviados por un usuario hoy."""
        hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.count(Mensaje.id))
            .join(Conversacion)
            .where(
                and_(
                    Conversacion.usuario_id == usuario_id,
                    Mensaje.role == "user",
                    Mensaje.created_at >= hoy_inicio,
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_tokens_usados_hoy(self, usuario_id: int) -> int:
        """Calcula tokens usados por un usuario hoy."""
        hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.coalesce(func.sum(Mensaje.tokens_usados), 0))
            .join(Conversacion)
            .where(
                and_(
                    Conversacion.usuario_id == usuario_id,
                    Mensaje.created_at >= hoy_inicio,
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_tiempo_respuesta_promedio(self) -> Optional[float]:
        """Calcula el tiempo de respuesta promedio."""
        result = await self.db.execute(
            select(func.avg(Mensaje.tiempo_respuesta_ms))
            .where(
                and_(
                    Mensaje.role == "assistant",
                    Mensaje.tiempo_respuesta_ms.is_not(None),
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_tasa_utilidad(self) -> float:
        """Calcula la tasa de mensajes marcados como útiles."""
        # Total de mensajes con feedback
        result_total = await self.db.execute(
            select(func.count(Mensaje.id))
            .where(
                and_(
                    Mensaje.role == "assistant",
                    Mensaje.util.is_not(None),
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        total = result_total.scalar_one()
        
        if total == 0:
            return 0.0
        
        # Mensajes útiles
        result_utiles = await self.db.execute(
            select(func.count(Mensaje.id))
            .where(
                and_(
                    Mensaje.role == "assistant",
                    Mensaje.util == True,
                    Mensaje.deleted_at.is_(None)
                )
            )
        )
        utiles = result_utiles.scalar_one()
        
        return (utiles / total) * 100

    async def update(self, mensaje: Mensaje) -> Mensaje:
        """Actualiza un mensaje."""
        await self.db.commit()
        await self.db.refresh(mensaje)
        return mensaje

    async def delete_by_conversacion(self, conversacion_id: int) -> None:
        """Elimina todos los mensajes de una conversación."""
        result = await self.db.execute(
            select(Mensaje).where(Mensaje.conversacion_id == conversacion_id)
        )
        mensajes = result.scalars().all()
        
        for mensaje in mensajes:
            mensaje.deleted_at = datetime.utcnow()
        
        await self.db.commit()
