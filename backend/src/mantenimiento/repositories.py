"""
Repositorio para operaciones de base de datos de mantenimiento.
"""
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.mantenimiento.models import Mantenimiento
from src.shared.constants import TipoMantenimiento, EstadoMantenimiento


class MantenimientoRepository:
    """Repositorio para gestión de mantenimientos."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        """Crea un nuevo mantenimiento."""
        self.db.add(mantenimiento)
        await self.db.commit()
        await self.db.refresh(mantenimiento)
        return mantenimiento

    async def get_by_id(self, mantenimiento_id: int) -> Optional[Mantenimiento]:
        """Obtiene un mantenimiento por ID."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.id == mantenimiento_id,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_codigo(self, codigo: str) -> Optional[Mantenimiento]:
        """Obtiene un mantenimiento por código."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.codigo == codigo,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_moto(
        self,
        moto_id: int,
        skip: int = 0,
        limit: int = 100,
        solo_activos: bool = False,
        solo_pendientes: bool = False
    ) -> List[Mantenimiento]:
        """Obtiene mantenimientos de una moto."""
        query = select(Mantenimiento).where(
            and_(
                Mantenimiento.moto_id == moto_id,
                Mantenimiento.deleted_at.is_(None)
            )
        )
        
        if solo_activos:
            query = query.where(
                Mantenimiento.estado.in_([
                    EstadoMantenimiento.PENDIENTE,
                    EstadoMantenimiento.PROGRAMADO,
                    EstadoMantenimiento.EN_PROCESO
                ])
            )
        
        if solo_pendientes:
            query = query.where(Mantenimiento.estado == EstadoMantenimiento.PENDIENTE)
        
        query = query.order_by(Mantenimiento.fecha_programada.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pendientes(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mantenimiento]:
        """Obtiene todos los mantenimientos pendientes."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.estado == EstadoMantenimiento.PENDIENTE,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.prioridad.desc(), Mantenimiento.fecha_programada)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_vencidos(self, skip: int = 0, limit: int = 100) -> List[Mantenimiento]:
        """Obtiene mantenimientos vencidos."""
        hoy = date.today()
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.fecha_vencimiento < hoy,
                    Mantenimiento.estado != EstadoMantenimiento.COMPLETADO,
                    Mantenimiento.estado != EstadoMantenimiento.CANCELADO,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.fecha_vencimiento)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_urgentes(self, skip: int = 0, limit: int = 100) -> List[Mantenimiento]:
        """Obtiene mantenimientos urgentes."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.es_urgente == True,
                    Mantenimiento.estado != EstadoMantenimiento.COMPLETADO,
                    Mantenimiento.estado != EstadoMantenimiento.CANCELADO,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.prioridad.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_proximos_a_vencer(
        self,
        dias: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mantenimiento]:
        """Obtiene mantenimientos próximos a vencer."""
        from datetime import timedelta
        fecha_limite = date.today() + timedelta(days=dias)
        
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.fecha_vencimiento.is_not(None),
                    Mantenimiento.fecha_vencimiento <= fecha_limite,
                    Mantenimiento.fecha_vencimiento >= date.today(),
                    Mantenimiento.estado != EstadoMantenimiento.COMPLETADO,
                    Mantenimiento.estado != EstadoMantenimiento.CANCELADO,
                    Mantenimiento.alerta_enviada == False,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.fecha_vencimiento)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recomendados_ia(
        self,
        moto_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mantenimiento]:
        """Obtiene mantenimientos recomendados por IA."""
        query = select(Mantenimiento).where(
            and_(
                Mantenimiento.recomendado_por_ia == True,
                Mantenimiento.deleted_at.is_(None)
            )
        )
        
        if moto_id:
            query = query.where(Mantenimiento.moto_id == moto_id)
        
        query = query.order_by(Mantenimiento.confianza_prediccion.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_tipo(
        self,
        tipo: TipoMantenimiento,
        skip: int = 0,
        limit: int = 100
    ) -> List[Mantenimiento]:
        """Obtiene mantenimientos por tipo."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.tipo == tipo,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.fecha_programada.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_historial_moto(
        self,
        moto_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Mantenimiento]:
        """Obtiene el historial completo de mantenimientos de una moto."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.moto_id == moto_id,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ultimo_por_tipo(
        self,
        moto_id: int,
        tipo: TipoMantenimiento
    ) -> Optional[Mantenimiento]:
        """Obtiene el último mantenimiento de un tipo específico."""
        result = await self.db.execute(
            select(Mantenimiento)
            .where(
                and_(
                    Mantenimiento.moto_id == moto_id,
                    Mantenimiento.tipo == tipo,
                    Mantenimiento.estado == EstadoMantenimiento.COMPLETADO,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
            .order_by(Mantenimiento.fecha_completado.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_moto(self, moto_id: int) -> int:
        """Cuenta mantenimientos de una moto."""
        result = await self.db.execute(
            select(func.count(Mantenimiento.id))
            .where(
                and_(
                    Mantenimiento.moto_id == moto_id,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def count_by_estado(self, estado: EstadoMantenimiento) -> int:
        """Cuenta mantenimientos por estado."""
        result = await self.db.execute(
            select(func.count(Mantenimiento.id))
            .where(
                and_(
                    Mantenimiento.estado == estado,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()

    async def get_stats_by_tipo(self) -> dict:
        """Obtiene estadísticas por tipo de mantenimiento."""
        result = await self.db.execute(
            select(
                Mantenimiento.tipo,
                func.count(Mantenimiento.id).label("count")
            )
            .where(Mantenimiento.deleted_at.is_(None))
            .group_by(Mantenimiento.tipo)
        )
        return {row.tipo.value: row.count for row in result}

    async def get_costo_total(self, moto_id: Optional[int] = None) -> float:
        """Obtiene el costo total de mantenimientos."""
        query = select(func.coalesce(func.sum(Mantenimiento.costo_real), 0))
        
        if moto_id:
            query = query.where(
                and_(
                    Mantenimiento.moto_id == moto_id,
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        else:
            query = query.where(Mantenimiento.deleted_at.is_(None))
        
        result = await self.db.execute(query)
        valor = result.scalar_one()
        return float(valor) if valor is not None else 0.0

    async def get_duracion_promedio(self) -> Optional[float]:
        """Calcula la duración promedio de mantenimientos completados."""
        result = await self.db.execute(
            select(
                Mantenimiento.fecha_inicio,
                Mantenimiento.fecha_completado
            )
            .where(
                and_(
                    Mantenimiento.estado == EstadoMantenimiento.COMPLETADO,
                    Mantenimiento.fecha_inicio.is_not(None),
                    Mantenimiento.fecha_completado.is_not(None),
                    Mantenimiento.deleted_at.is_(None)
                )
            )
        )
        
        duraciones = []
        for row in result:
            if row.fecha_inicio and row.fecha_completado:
                delta = row.fecha_completado - row.fecha_inicio
                duraciones.append(delta.total_seconds() / 3600)  # horas
        
        if not duraciones:
            return None
        
        return sum(duraciones) / len(duraciones)

    async def update(self, mantenimiento: Mantenimiento) -> Mantenimiento:
        """Actualiza un mantenimiento."""
        await self.db.commit()
        await self.db.refresh(mantenimiento)
        return mantenimiento

    async def delete(self, mantenimiento: Mantenimiento) -> None:
        """Soft delete de un mantenimiento."""
        mantenimiento.deleted_at = datetime.utcnow()
        await self.db.commit()

    async def marcar_alerta_enviada(self, mantenimiento_id: int) -> None:
        """Marca una alerta como enviada."""
        result = await self.db.execute(
            select(Mantenimiento).where(Mantenimiento.id == mantenimiento_id)
        )
        mantenimiento = result.scalar_one_or_none()
        if mantenimiento:
            mantenimiento.alerta_enviada = True
            mantenimiento.fecha_alerta_enviada = datetime.utcnow()
            await self.db.commit()
