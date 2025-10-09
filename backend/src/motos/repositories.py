"""
Repositorio para gestión de motos en la base de datos.
"""
from typing import Optional, Sequence
from datetime import datetime
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Moto
from ..auth.models import Usuario


class MotoRepository:
    """Repositorio para operaciones CRUD de motos."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, moto_data: dict) -> Moto:
        """
        Crea una nueva moto.
        
        Args:
            moto_data: Diccionario con datos de la moto
            
        Returns:
            Moto creada
        """
        moto = Moto(**moto_data)
        self.session.add(moto)
        await self.session.commit()
        await self.session.refresh(moto)
        return moto
    
    async def get_by_id(
        self,
        moto_id: int,
        include_deleted: bool = False,
        load_usuario: bool = True
    ) -> Optional[Moto]:
        """
        Obtiene una moto por ID.
        
        Args:
            moto_id: ID de la moto
            include_deleted: Si incluir motos eliminadas
            load_usuario: Si cargar la relación con usuario
            
        Returns:
            Moto o None si no existe
        """
        query = select(Moto).where(Moto.id == moto_id)
        
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        if load_usuario:
            query = query.options(selectinload(Moto.usuario))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_vin(self, vin: str, include_deleted: bool = False) -> Optional[Moto]:
        """
        Obtiene una moto por VIN.
        
        Args:
            vin: VIN de la moto
            include_deleted: Si incluir motos eliminadas
            
        Returns:
            Moto o None si no existe
        """
        query = select(Moto).where(Moto.vin == vin.upper())
        
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_placa(self, placa: str, include_deleted: bool = False) -> Optional[Moto]:
        """
        Obtiene una moto por placa.
        
        Args:
            placa: Placa de la moto
            include_deleted: Si incluir motos eliminadas
            
        Returns:
            Moto o None si no existe
        """
        query = select(Moto).where(Moto.placa == placa.upper())
        
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_motos(
        self,
        usuario_id: Optional[int] = None,
        modelo: Optional[str] = None,
        año_desde: Optional[int] = None,
        año_hasta: Optional[int] = None,
        vin: Optional[str] = None,
        placa: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc",
        include_deleted: bool = False,
        load_usuario: bool = True
    ) -> Sequence[Moto]:
        """
        Lista motos con filtros y paginación.
        
        Args:
            usuario_id: Filtrar por usuario
            modelo: Filtrar por modelo (búsqueda parcial)
            año_desde: Año de fabricación desde
            año_hasta: Año de fabricación hasta
            vin: Buscar por VIN
            placa: Buscar por placa
            skip: Registros a saltar
            limit: Registros a retornar
            order_by: Campo para ordenar
            order_direction: Dirección del ordenamiento
            include_deleted: Si incluir motos eliminadas
            load_usuario: Si cargar la relación con usuario
            
        Returns:
            Lista de motos
        """
        query = select(Moto)
        
        # Filtros
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        if usuario_id is not None:
            query = query.where(Moto.usuario_id == usuario_id)
        
        if modelo:
            query = query.where(Moto.modelo.ilike(f"%{modelo}%"))
        
        if año_desde is not None:
            query = query.where(Moto.año >= año_desde)
        
        if año_hasta is not None:
            query = query.where(Moto.año <= año_hasta)
        
        if vin:
            query = query.where(Moto.vin == vin.upper())
        
        if placa:
            query = query.where(Moto.placa == placa.upper())
        
        # Ordenamiento
        order_column = getattr(Moto, order_by, Moto.created_at)
        if order_direction == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Relaciones
        if load_usuario:
            query = query.options(selectinload(Moto.usuario))
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_motos(
        self,
        usuario_id: Optional[int] = None,
        modelo: Optional[str] = None,
        año_desde: Optional[int] = None,
        año_hasta: Optional[int] = None,
        vin: Optional[str] = None,
        placa: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        """
        Cuenta motos que coinciden con los filtros.
        
        Args:
            usuario_id: Filtrar por usuario
            modelo: Filtrar por modelo
            año_desde: Año de fabricación desde
            año_hasta: Año de fabricación hasta
            vin: Buscar por VIN
            placa: Buscar por placa
            include_deleted: Si incluir motos eliminadas
            
        Returns:
            Número de motos
        """
        query = select(func.count(Moto.id))
        
        # Filtros
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        if usuario_id is not None:
            query = query.where(Moto.usuario_id == usuario_id)
        
        if modelo:
            query = query.where(Moto.modelo.ilike(f"%{modelo}%"))
        
        if año_desde is not None:
            query = query.where(Moto.año >= año_desde)
        
        if año_hasta is not None:
            query = query.where(Moto.año <= año_hasta)
        
        if vin:
            query = query.where(Moto.vin == vin.upper())
        
        if placa:
            query = query.where(Moto.placa == placa.upper())
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def update(self, moto: Moto, update_data: dict) -> Moto:
        """
        Actualiza una moto.
        
        Args:
            moto: Moto a actualizar
            update_data: Datos a actualizar
            
        Returns:
            Moto actualizada
        """
        for key, value in update_data.items():
            if hasattr(moto, key):
                setattr(moto, key, value)
        
        moto.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(moto)
        return moto
    
    async def delete(self, moto: Moto, soft: bool = True) -> None:
        """
        Elimina una moto (soft delete por defecto).
        
        Args:
            moto: Moto a eliminar
            soft: Si hacer soft delete o hard delete
        """
        if soft:
            moto.deleted_at = datetime.utcnow()
            await self.session.commit()
        else:
            await self.session.delete(moto)
            await self.session.commit()
    
    async def vin_exists(self, vin: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si un VIN ya existe.
        
        Args:
            vin: VIN a verificar
            exclude_id: ID de moto a excluir (para updates)
            
        Returns:
            True si existe, False si no
        """
        query = select(func.count(Moto.id)).where(
            Moto.vin == vin.upper(),
            Moto.deleted_at.is_(None)
        )
        
        if exclude_id is not None:
            query = query.where(Moto.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def placa_exists(self, placa: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verifica si una placa ya existe.
        
        Args:
            placa: Placa a verificar
            exclude_id: ID de moto a excluir (para updates)
            
        Returns:
            True si existe, False si no
        """
        query = select(func.count(Moto.id)).where(
            Moto.placa == placa.upper(),
            Moto.deleted_at.is_(None)
        )
        
        if exclude_id is not None:
            query = query.where(Moto.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def get_motos_by_usuario(
        self,
        usuario_id: int,
        include_deleted: bool = False
    ) -> Sequence[Moto]:
        """
        Obtiene todas las motos de un usuario.
        
        Args:
            usuario_id: ID del usuario
            include_deleted: Si incluir motos eliminadas
            
        Returns:
            Lista de motos del usuario
        """
        query = select(Moto).where(Moto.usuario_id == usuario_id)
        
        if not include_deleted:
            query = query.where(Moto.deleted_at.is_(None))
        
        query = query.order_by(desc(Moto.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_stats(self) -> dict:
        """
        Obtiene estadísticas de motos.
        
        Returns:
            Diccionario con estadísticas
        """
        # Total de motos
        total_query = select(func.count(Moto.id)).where(Moto.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_motos = total_result.scalar_one()
        
        # Motos por año
        año_query = select(
            Moto.año,
            func.count(Moto.id).label("count")
        ).where(
            Moto.deleted_at.is_(None)
        ).group_by(Moto.año).order_by(desc("count"))
        
        año_result = await self.session.execute(año_query)
        motos_por_año = {row.año: row.count for row in año_result}
        
        # Kilometraje promedio
        km_query = select(func.avg(Moto.kilometraje)).where(Moto.deleted_at.is_(None))
        km_result = await self.session.execute(km_query)
        kilometraje_promedio = km_result.scalar_one() or 0.0
        
        # Modelos populares
        modelo_query = select(
            Moto.modelo,
            func.count(Moto.id).label("count")
        ).where(
            Moto.deleted_at.is_(None)
        ).group_by(Moto.modelo).order_by(desc("count")).limit(10)
        
        modelo_result = await self.session.execute(modelo_query)
        modelos_populares = [
            {"modelo": row.modelo, "count": row.count}
            for row in modelo_result
        ]
        
        return {
            "total_motos": total_motos,
            "motos_por_año": motos_por_año,
            "kilometraje_promedio": float(kilometraje_promedio),
            "modelos_populares": modelos_populares
        }
