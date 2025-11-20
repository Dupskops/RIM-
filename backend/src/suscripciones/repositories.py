"""
Repositorio para gestión de suscripciones en la base de datos.
"""
from typing import Optional, Sequence
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Suscripcion, Plan, Caracteristica


class SuscripcionRepository:
    """Repositorio para operaciones CRUD de suscripciones."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_usuario_id(self, usuario_id: int) -> Optional[Suscripcion]:
        """Obtiene la suscripción más reciente de un usuario con eager loading completo."""
        stmt = (
            select(Suscripcion)
            .options(
                selectinload(Suscripcion.plan).selectinload(Plan.caracteristicas)
            )
            .where(Suscripcion.usuario_id == usuario_id)
            .order_by(desc(Suscripcion.id))
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()


class PlanesRepository:
    """Repositorio para operaciones CRUD de planes."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_planes(self) -> Sequence[Plan]:
        """Retorna una lista de objetos Plan (ORM) con eager loading de características."""
        stmt = select(Plan).options(selectinload(Plan.caracteristicas))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_plan_by_nombre(self, nombre_plan: str) -> Optional[Plan]:
        """Busca un plan por nombre (case-insensitive) con eager loading de características.
        
        Args:
            nombre_plan: Nombre del plan a buscar (ej: "FREE", "Pro", "Premium")
            
        Returns:
            Plan encontrado o None
        """
        stmt = (
            select(Plan)
            .options(selectinload(Plan.caracteristicas))
            .where(func.lower(Plan.nombre_plan) == nombre_plan.lower())
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """Busca un plan por ID con eager loading de características.
        
        Args:
            plan_id: ID del plan
            
        Returns:
            Plan encontrado o None
        """
        stmt = (
            select(Plan)
            .options(selectinload(Plan.caracteristicas))
            .where(Plan.id == plan_id)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()


class CaracteristicaRepository:
    """Repositorio para operaciones CRUD de características."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> Sequence[Caracteristica]:
        """Retorna todas las características disponibles."""

        stmt = select(Caracteristica)
        res = await self.session.execute(stmt)
        return res.scalars().all()


__all__ = [
    "SuscripcionRepository",
    "PlanesRepository",
    "CaracteristicaRepository",
]

