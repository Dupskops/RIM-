"""
Repositorio para gestión de suscripciones en la base de datos.
"""
from typing import Optional, Sequence
from datetime import datetime
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Suscripcion


class SuscripcionRepository:
    """Repositorio para operaciones CRUD de suscripciones."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, suscripcion_data: dict) -> Suscripcion:
        """
        Crea una nueva suscripción.
        
        Args:
            suscripcion_data: Diccionario con datos de la suscripción
            
        Returns:
            Suscripción creada
        """
        suscripcion = Suscripcion(**suscripcion_data)
        self.session.add(suscripcion)
        await self.session.commit()
        await self.session.refresh(suscripcion)
        return suscripcion
    
    async def get_by_id(
        self,
        suscripcion_id: int,
        include_deleted: bool = False
    ) -> Optional[Suscripcion]:
        """
        Obtiene una suscripción por ID.
        
        Args:
            suscripcion_id: ID de la suscripción
            include_deleted: Si incluir suscripciones eliminadas
            
        Returns:
            Suscripción o None si no existe
        """
        query = select(Suscripcion).where(Suscripcion.id == suscripcion_id)
        
        if not include_deleted:
            query = query.where(Suscripcion.deleted_at.is_(None))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_by_usuario(self, usuario_id: int) -> Optional[Suscripcion]:
        """
        Obtiene la suscripción activa de un usuario.
        
        Args:
            usuario_id: ID del usuario (INTEGER)
            
        Returns:
            Suscripción activa o None
        """
        query = select(Suscripcion).where(
            Suscripcion.usuario_id == usuario_id,
            Suscripcion.status == SuscripcionStatus.ACTIVE,
            Suscripcion.deleted_at.is_(None)
        ).order_by(desc(Suscripcion.created_at))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_suscripciones(
        self,
        usuario_id: Optional[int] = None,  # INTEGER
        plan: Optional[str] = None,
        status: Optional[str] = None,
        activas_only: bool = False,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc",
        include_deleted: bool = False
    ) -> Sequence[Suscripcion]:
        """
        Lista suscripciones con filtros y paginación.
        
        Args:
            usuario_id: Filtrar por usuario
            plan: Filtrar por plan
            status: Filtrar por estado
            activas_only: Solo suscripciones activas
            skip: Registros a saltar
            limit: Registros a retornar
            order_by: Campo para ordenar
            order_direction: Dirección del ordenamiento
            include_deleted: Si incluir suscripciones eliminadas
            
        Returns:
            Lista de suscripciones
        """
        query = select(Suscripcion)
        
        # Filtros
        if not include_deleted:
            query = query.where(Suscripcion.deleted_at.is_(None))
        
        if usuario_id is not None:
            query = query.where(Suscripcion.usuario_id == usuario_id)
        
        if plan:
            query = query.where(Suscripcion.plan == plan)
        
        if status:
            query = query.where(Suscripcion.status == status)
        
        if activas_only:
            query = query.where(
                Suscripcion.status == SuscripcionStatus.ACTIVE,
                or_(
                    Suscripcion.end_date.is_(None),
                    Suscripcion.end_date > datetime.utcnow()
                )
            )
        
        # Ordenamiento
        order_column = getattr(Suscripcion, order_by, Suscripcion.created_at)
        if order_direction == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_suscripciones(
        self,
        usuario_id: Optional[int] = None,  # INTEGER
        plan: Optional[str] = None,
        status: Optional[str] = None,
        activas_only: bool = False,
        include_deleted: bool = False
    ) -> int:
        """
        Cuenta suscripciones que coinciden con los filtros.
        
        Args:
            usuario_id: Filtrar por usuario
            plan: Filtrar por plan
            status: Filtrar por estado
            activas_only: Solo suscripciones activas
            include_deleted: Si incluir suscripciones eliminadas
            
        Returns:
            Número de suscripciones
        """
        query = select(func.count(Suscripcion.id))
        
        # Filtros
        if not include_deleted:
            query = query.where(Suscripcion.deleted_at.is_(None))
        
        if usuario_id is not None:
            query = query.where(Suscripcion.usuario_id == usuario_id)
        
        if plan:
            query = query.where(Suscripcion.plan == plan)
        
        if status:
            query = query.where(Suscripcion.status == status)
        
        if activas_only:
            query = query.where(
                Suscripcion.status == SuscripcionStatus.ACTIVE,
                or_(
                    Suscripcion.end_date.is_(None),
                    Suscripcion.end_date > datetime.utcnow()
                )
            )
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def update(self, suscripcion: Suscripcion, update_data: dict) -> Suscripcion:
        """
        Actualiza una suscripción.
        
        Args:
            suscripcion: Suscripción a actualizar
            update_data: Datos a actualizar
            
        Returns:
            Suscripción actualizada
        """
        for key, value in update_data.items():
            if hasattr(suscripcion, key):
                setattr(suscripcion, key, value)
        
        suscripcion.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(suscripcion)
        return suscripcion
    
    async def delete(self, suscripcion: Suscripcion, soft: bool = True) -> None:
        """
        Elimina una suscripción (soft delete por defecto).
        
        Args:
            suscripcion: Suscripción a eliminar
            soft: Si hacer soft delete o hard delete
        """
        if soft:
            suscripcion.deleted_at = datetime.utcnow()
            await self.session.commit()
        else:
            await self.session.delete(suscripcion)
            await self.session.commit()
    
    async def transaction_exists(self, transaction_id: str) -> bool:
        """
        Verifica si un ID de transacción ya existe.
        
        Args:
            transaction_id: ID de transacción a verificar
            
        Returns:
            True si existe, False si no
        """
        query = select(func.count(Suscripcion.id)).where(
            Suscripcion.transaction_id == transaction_id,
            Suscripcion.deleted_at.is_(None)
        )
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def get_expired_suscripciones(self) -> Sequence[Suscripcion]:
        """
        Obtiene suscripciones que han expirado pero aún tienen status active.
        
        Returns:
            Lista de suscripciones expiradas
        """
        query = select(Suscripcion).where(
            Suscripcion.status == SuscripcionStatus.ACTIVE,
            Suscripcion.end_date.is_not(None),
            Suscripcion.end_date < datetime.utcnow(),
            Suscripcion.deleted_at.is_(None)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_stats(self) -> dict:
        """
        Obtiene estadísticas de suscripciones.
        
        Returns:
            Diccionario con estadísticas
        """
        # Total de suscripciones
        total_query = select(func.count(Suscripcion.id)).where(
            Suscripcion.deleted_at.is_(None)
        )
        total_result = await self.session.execute(total_query)
        total_suscripciones = total_result.scalar_one()
        
        # Suscripciones activas
        activas_query = select(func.count(Suscripcion.id)).where(
            Suscripcion.status == SuscripcionStatus.ACTIVE,
            Suscripcion.deleted_at.is_(None)
        )
        activas_result = await self.session.execute(activas_query)
        suscripciones_activas = activas_result.scalar_one()
        
        # Suscripciones freemium
        freemium_query = select(func.count(Suscripcion.id)).where(
            Suscripcion.plan == PlanType.FREEMIUM,
            Suscripcion.deleted_at.is_(None)
        )
        freemium_result = await self.session.execute(freemium_query)
        suscripciones_freemium = freemium_result.scalar_one()
        
        # Suscripciones premium
        premium_query = select(func.count(Suscripcion.id)).where(
            Suscripcion.plan == PlanType.PREMIUM,
            Suscripcion.deleted_at.is_(None)
        )
        premium_result = await self.session.execute(premium_query)
        suscripciones_premium = premium_result.scalar_one()
        
        # Ingresos totales
        ingresos_query = select(func.sum(Suscripcion.precio)).where(
            Suscripcion.plan == PlanType.PREMIUM,
            Suscripcion.deleted_at.is_(None)
        )
        ingresos_result = await self.session.execute(ingresos_query)
        ingresos_totales = ingresos_result.scalar_one() or 0.0
        
        # Tasa de conversión
        tasa_conversion = 0.0
        if total_suscripciones > 0:
            tasa_conversion = (suscripciones_premium / total_suscripciones) * 100
        
        return {
            "total_suscripciones": total_suscripciones,
            "suscripciones_activas": suscripciones_activas,
            "suscripciones_freemium": suscripciones_freemium,
            "suscripciones_premium": suscripciones_premium,
            "ingresos_totales": float(ingresos_totales),
            "tasa_conversion": round(tasa_conversion, 2)
        }

class PlanesRepository:
    """Repositorio para operaciones CRUD de planes."""
    
    def __init__(self, session: AsyncSession):
        self.session = session