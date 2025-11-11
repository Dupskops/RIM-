"""
Repositorio para gestión de suscripciones en la base de datos.
"""
from typing import Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Suscripcion, Plan


class SuscripcionRepository:
    """Repositorio para operaciones CRUD de suscripciones."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_usuario_id(self, usuario_id: int) -> Optional[Suscripcion]:
        """Obtiene la suscripción más reciente de un usuario con eager loading completo."""
        from sqlalchemy.orm import selectinload
        from sqlalchemy import desc
        
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
        """Retorna una lista de objetos Plan (ORM)."""
        stmt = select(Plan)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_plan_by_nombre(self, nombre_plan: str) -> Optional[Plan]:
        """Busca un plan por nombre (case-insensitive).
        
        Args:
            nombre_plan: Nombre del plan a buscar (ej: "FREE", "Pro", "Premium")
            
        Returns:
            Plan encontrado o None
        """
        stmt = select(Plan).where(
            func.lower(Plan.nombre_plan) == nombre_plan.lower()
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        """Busca un plan por ID.
        
        Args:
            plan_id: ID del plan
            
        Returns:
            Plan encontrado o None
        """
        stmt = select(Plan).where(Plan.id == plan_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()


__all__ = [
    "SuscripcionRepository",
    "PlanesRepository",
]

