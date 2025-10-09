"""
Repositorios para el módulo de notificaciones.
"""
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.notificaciones.models import (
    Notificacion,
    PreferenciaNotificacion,
    EstadoNotificacion,
    CanalNotificacion,
    TipoNotificacion
)


class NotificacionRepository:
    """Repositorio para gestionar notificaciones."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, notificacion: Notificacion) -> Notificacion:
        """Crea una nueva notificación."""
        self.session.add(notificacion)
        await self.session.commit()
        await self.session.refresh(notificacion)
        return notificacion

    async def create_many(self, notificaciones: List[Notificacion]) -> List[Notificacion]:
        """Crea múltiples notificaciones."""
        self.session.add_all(notificaciones)
        await self.session.commit()
        for notif in notificaciones:
            await self.session.refresh(notif)
        return notificaciones

    async def get_by_id(self, notificacion_id: int) -> Optional[Notificacion]:
        """Obtiene una notificación por ID."""
        result = await self.session.execute(
            select(Notificacion).where(Notificacion.id == notificacion_id)
        )
        return result.scalar_one_or_none()

    async def get_by_usuario(
        self,
        usuario_id: int,
        solo_no_leidas: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> List[Notificacion]:
        """Obtiene notificaciones de un usuario."""
        query = select(Notificacion).where(Notificacion.usuario_id == usuario_id)
        
        if solo_no_leidas:
            query = query.where(Notificacion.leida == False)
        
        query = query.order_by(Notificacion.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_usuario(
        self,
        usuario_id: int,
        solo_no_leidas: bool = False
    ) -> int:
        """Cuenta notificaciones de un usuario."""
        query = select(func.count(Notificacion.id)).where(
            Notificacion.usuario_id == usuario_id
        )
        
        if solo_no_leidas:
            query = query.where(Notificacion.leida == False)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_estado(
        self,
        estado: EstadoNotificacion,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notificacion]:
        """Obtiene notificaciones por estado."""
        query = select(Notificacion).where(Notificacion.estado == estado)
        query = query.order_by(Notificacion.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pendientes_envio(self, limit: int = 100) -> List[Notificacion]:
        """Obtiene notificaciones pendientes de envío."""
        query = select(Notificacion).where(
            and_(
                Notificacion.estado == EstadoNotificacion.PENDIENTE,
                Notificacion.enviada == False
            )
        )
        query = query.order_by(Notificacion.created_at.asc())
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_fallidas_reintentables(self, limit: int = 100) -> List[Notificacion]:
        """Obtiene notificaciones fallidas que pueden reintentarse."""
        query = select(Notificacion).where(
            and_(
                Notificacion.estado == EstadoNotificacion.FALLIDA,
                Notificacion.intentos_envio < 3,
                or_(
                    Notificacion.expira_en == None,
                    Notificacion.expira_en > datetime.utcnow()
                )
            )
        )
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def marcar_como_leida(self, notificacion_id: int) -> bool:
        """Marca una notificación como leída."""
        notificacion = await self.get_by_id(notificacion_id)
        if notificacion:
            notificacion.marcar_como_leida()
            await self.session.commit()
            return True
        return False

    async def marcar_varias_como_leidas(self, notificacion_ids: List[int]) -> int:
        """Marca varias notificaciones como leídas."""
        result = await self.session.execute(
            select(Notificacion).where(Notificacion.id.in_(notificacion_ids))
        )
        notificaciones = result.scalars().all()
        
        count = 0
        for notif in notificaciones:
            notif.marcar_como_leida()
            count += 1
        
        await self.session.commit()
        return count

    async def marcar_todas_como_leidas(self, usuario_id: int) -> int:
        """Marca todas las notificaciones de un usuario como leídas."""
        result = await self.session.execute(
            select(Notificacion).where(
                and_(
                    Notificacion.usuario_id == usuario_id,
                    Notificacion.leida == False
                )
            )
        )
        notificaciones = result.scalars().all()
        
        count = 0
        for notif in notificaciones:
            notif.marcar_como_leida()
            count += 1
        
        await self.session.commit()
        return count

    async def update(self, notificacion: Notificacion) -> Notificacion:
        """Actualiza una notificación."""
        await self.session.commit()
        await self.session.refresh(notificacion)
        return notificacion

    async def delete(self, notificacion_id: int) -> bool:
        """Elimina una notificación."""
        notificacion = await self.get_by_id(notificacion_id)
        if notificacion:
            await self.session.delete(notificacion)
            await self.session.commit()
            return True
        return False

    async def delete_antiguas(self, dias: int = 30) -> int:
        """Elimina notificaciones antiguas leídas."""
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        
        result = await self.session.execute(
            select(Notificacion).where(
                and_(
                    Notificacion.leida == True,
                    Notificacion.created_at < fecha_limite
                )
            )
        )
        notificaciones = result.scalars().all()
        
        count = 0
        for notif in notificaciones:
            await self.session.delete(notif)
            count += 1
        
        await self.session.commit()
        return count

    async def get_stats(self, usuario_id: int) -> dict:
        """Obtiene estadísticas de notificaciones de un usuario."""
        # Total
        total = await self.count_by_usuario(usuario_id)
        no_leidas = await self.count_by_usuario(usuario_id, solo_no_leidas=True)
        leidas = total - no_leidas
        
        # Por tipo
        result_tipo = await self.session.execute(
            select(Notificacion.tipo, func.count(Notificacion.id))
            .where(Notificacion.usuario_id == usuario_id)
            .group_by(Notificacion.tipo)
        )
        por_tipo = {tipo: count for tipo, count in result_tipo.all()}
        
        # Por canal
        result_canal = await self.session.execute(
            select(Notificacion.canal, func.count(Notificacion.id))
            .where(Notificacion.usuario_id == usuario_id)
            .group_by(Notificacion.canal)
        )
        por_canal = {canal: count for canal, count in result_canal.all()}
        
        # Por estado
        result_estado = await self.session.execute(
            select(Notificacion.estado, func.count(Notificacion.id))
            .where(Notificacion.usuario_id == usuario_id)
            .group_by(Notificacion.estado)
        )
        por_estado = {estado: count for estado, count in result_estado.all()}
        
        return {
            "total": total,
            "no_leidas": no_leidas,
            "leidas": leidas,
            "por_tipo": por_tipo,
            "por_canal": por_canal,
            "por_estado": por_estado,
        }


class PreferenciaNotificacionRepository:
    """Repositorio para preferencias de notificaciones."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, preferencia: PreferenciaNotificacion) -> PreferenciaNotificacion:
        """Crea preferencias de notificación."""
        self.session.add(preferencia)
        await self.session.commit()
        await self.session.refresh(preferencia)
        return preferencia

    async def get_by_usuario(self, usuario_id: int) -> Optional[PreferenciaNotificacion]:
        """Obtiene las preferencias de un usuario."""
        result = await self.session.execute(
            select(PreferenciaNotificacion).where(
                PreferenciaNotificacion.usuario_id == usuario_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, usuario_id: int) -> PreferenciaNotificacion:
        """Obtiene o crea preferencias de un usuario."""
        preferencia = await self.get_by_usuario(usuario_id)
        
        if not preferencia:
            preferencia = PreferenciaNotificacion(usuario_id=usuario_id)
            self.session.add(preferencia)
            await self.session.commit()
            await self.session.refresh(preferencia)
        
        return preferencia

    async def update(self, preferencia: PreferenciaNotificacion) -> PreferenciaNotificacion:
        """Actualiza preferencias de notificación."""
        await self.session.commit()
        await self.session.refresh(preferencia)
        return preferencia
