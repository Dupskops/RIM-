"""
Repositorio para operaciones de base de datos de fallas.
Capa de acceso a datos siguiendo patrón Repository.
"""
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Falla
from ..shared.constants import EstadoFalla, SeveridadFalla


class FallaRepository:
    """Repositorio para gestionar fallas en la base de datos."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio.
        
        Args:
            session: Sesión async de SQLAlchemy
        """
        self.session = session
    
    async def create(self, falla: Falla) -> Falla:
        """
        Crea una nueva falla.
        
        Args:
            falla: Objeto Falla a crear
            
        Returns:
            Falla creada con ID asignado
        """
        self.session.add(falla)
        await self.session.commit()
        await self.session.refresh(falla)
        return falla
    
    async def get_by_id(self, falla_id: int) -> Optional[Falla]:
        """
        Obtiene una falla por su ID.
        
        Args:
            falla_id: ID de la falla
            
        Returns:
            Falla encontrada o None
        """
        result = await self.session.execute(
            select(Falla).where(
                and_(
                    Falla.id == falla_id,
                    Falla.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_codigo(self, codigo: str) -> Optional[Falla]:
        """
        Obtiene una falla por su código único.
        
        Args:
            codigo: Código de la falla
            
        Returns:
            Falla encontrada o None
        """
        result = await self.session.execute(
            select(Falla).where(
                and_(
                    Falla.codigo == codigo,
                    Falla.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_moto(
        self,
        moto_id: int,
        solo_activas: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Falla]:
        """
        Obtiene todas las fallas de una moto.
        
        Args:
            moto_id: ID de la moto
            solo_activas: Si True, solo fallas no resueltas
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de fallas
        """
        query = select(Falla).where(
            and_(
                Falla.moto_id == moto_id,
                Falla.deleted_at.is_(None)
            )
        )
        
        if solo_activas:
            query = query.where(Falla.estado != EstadoFalla.RESUELTA.value)
        
        query = query.order_by(Falla.fecha_deteccion.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_criticas_activas(self, moto_id: int) -> List[Falla]:
        """
        Obtiene fallas críticas activas de una moto.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Lista de fallas críticas sin resolver
        """
        result = await self.session.execute(
            select(Falla).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.severidad == SeveridadFalla.CRITICA.value,
                    Falla.estado != EstadoFalla.RESUELTA.value,
                    Falla.deleted_at.is_(None)
                )
            ).order_by(Falla.fecha_deteccion.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_tipo(
        self,
        moto_id: int,
        tipo: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Falla]:
        """
        Obtiene fallas de un tipo específico para una moto.
        
        Args:
            moto_id: ID de la moto
            tipo: Tipo de falla
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de fallas del tipo especificado
        """
        result = await self.session.execute(
            select(Falla).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.tipo == tipo,
                    Falla.deleted_at.is_(None)
                )
            ).order_by(Falla.fecha_deteccion.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_recientes(
        self,
        moto_id: int,
        dias: int = 30,
        limit: int = 50
    ) -> List[Falla]:
        """
        Obtiene fallas recientes de una moto.
        
        Args:
            moto_id: ID de la moto
            dias: Número de días hacia atrás
            limit: Número máximo de registros
            
        Returns:
            Lista de fallas recientes
        """
        fecha_desde = datetime.now(timezone.utc) - timedelta(days=dias)
        
        result = await self.session.execute(
            select(Falla).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.fecha_deteccion >= fecha_desde,
                    Falla.deleted_at.is_(None)
                )
            ).order_by(Falla.fecha_deteccion.desc()).limit(limit)
        )
        return list(result.scalars().all())
    
    async def update(self, falla: Falla) -> Falla:
        """
        Actualiza una falla existente.
        
        Args:
            falla: Objeto Falla con cambios
            
        Returns:
            Falla actualizada
        """
        await self.session.commit()
        await self.session.refresh(falla)
        return falla
    
    async def delete(self, falla_id: int) -> bool:
        """
        Elimina (soft delete) una falla.
        
        Args:
            falla_id: ID de la falla
            
        Returns:
            True si se eliminó, False si no existía
        """
        falla = await self.get_by_id(falla_id)
        if not falla:
            return False
        
        falla.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True
    
    async def count_by_moto(self, moto_id: int, solo_activas: bool = False) -> int:
        """
        Cuenta el número de fallas de una moto.
        
        Args:
            moto_id: ID de la moto
            solo_activas: Si True, solo cuenta fallas no resueltas
            
        Returns:
            Número de fallas
        """
        query = select(func.count(Falla.id)).where(
            and_(
                Falla.moto_id == moto_id,
                Falla.deleted_at.is_(None)
            )
        )
        
        if solo_activas:
            query = query.where(Falla.estado != EstadoFalla.RESUELTA.value)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_stats_by_tipo(self, moto_id: int) -> dict:
        """
        Obtiene estadísticas de fallas agrupadas por tipo.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Diccionario {tipo: count}
        """
        result = await self.session.execute(
            select(
                Falla.tipo,
                func.count(Falla.id).label("count")
            ).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.deleted_at.is_(None)
                )
            ).group_by(Falla.tipo)
        )
        
        return {row.tipo: row.count for row in result}
    
    async def get_stats_by_severidad(self, moto_id: int) -> dict:
        """
        Obtiene estadísticas de fallas agrupadas por severidad.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Diccionario {severidad: count}
        """
        result = await self.session.execute(
            select(
                Falla.severidad,
                func.count(Falla.id).label("count")
            ).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.deleted_at.is_(None)
                )
            ).group_by(Falla.severidad)
        )
        
        return {row.severidad: row.count for row in result}
    
    async def get_costo_total_reparaciones(self, moto_id: int) -> float:
        """
        Calcula el costo total de reparaciones de una moto.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Costo total
        """
        result = await self.session.execute(
            select(func.sum(Falla.costo_real)).where(
                and_(
                    Falla.moto_id == moto_id,
                    Falla.costo_real.isnot(None),
                    Falla.deleted_at.is_(None)
                )
            )
        )
        
        total = result.scalar_one()
        return float(total) if total else 0.0
