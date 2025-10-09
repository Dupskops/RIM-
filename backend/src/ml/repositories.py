"""
Repositorios para el módulo de ML.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.ml.models import Prediccion, EntrenamientoModelo, EstadoPrediccion, TipoPrediccion


class PrediccionRepository:
    """Repositorio para predicciones de ML."""
    
    async def create(self, db: AsyncSession, prediccion_data: Dict[str, Any]) -> Prediccion:
        """Crea una nueva predicción."""
        prediccion = Prediccion(**prediccion_data)
        db.add(prediccion)
        await db.commit()
        await db.refresh(prediccion)
        return prediccion
    
    async def get_by_id(self, db: AsyncSession, prediccion_id: int) -> Optional[Prediccion]:
        """Obtiene predicción por ID."""
        result = await db.execute(
            select(Prediccion).where(Prediccion.id == prediccion_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_moto(
        self,
        db: AsyncSession,
        moto_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediccion]:
        """Obtiene predicciones de una motocicleta."""
        result = await db.execute(
            select(Prediccion)
            .where(Prediccion.moto_id == moto_id)
            .order_by(desc(Prediccion.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_usuario(
        self,
        db: AsyncSession,
        usuario_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediccion]:
        """Obtiene predicciones de un usuario."""
        result = await db.execute(
            select(Prediccion)
            .where(Prediccion.usuario_id == usuario_id)
            .order_by(desc(Prediccion.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_tipo(
        self,
        db: AsyncSession,
        tipo: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Prediccion]:
        """Obtiene predicciones por tipo."""
        result = await db.execute(
            select(Prediccion)
            .where(Prediccion.tipo == tipo)
            .order_by(desc(Prediccion.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_criticas(
        self,
        db: AsyncSession,
        moto_id: Optional[int] = None,
        usuario_id: Optional[int] = None
    ) -> List[Prediccion]:
        """Obtiene predicciones críticas (confianza >= 0.85)."""
        query = select(Prediccion).where(
            and_(
                Prediccion.confianza >= 0.85,
                Prediccion.estado == EstadoPrediccion.PENDIENTE.value
            )
        )
        
        if moto_id:
            query = query.where(Prediccion.moto_id == moto_id)
        if usuario_id:
            query = query.where(Prediccion.usuario_id == usuario_id)
        
        query = query.order_by(desc(Prediccion.confianza))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_pendientes(
        self,
        db: AsyncSession,
        moto_id: Optional[int] = None
    ) -> List[Prediccion]:
        """Obtiene predicciones pendientes."""
        query = select(Prediccion).where(
            Prediccion.estado == EstadoPrediccion.PENDIENTE.value
        )
        
        if moto_id:
            query = query.where(Prediccion.moto_id == moto_id)
        
        query = query.order_by(desc(Prediccion.created_at))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self,
        db: AsyncSession,
        prediccion: Prediccion,
        update_data: Dict[str, Any]
    ) -> Prediccion:
        """Actualiza una predicción."""
        for key, value in update_data.items():
            setattr(prediccion, key, value)
        
        await db.commit()
        await db.refresh(prediccion)
        return prediccion
    
    async def marcar_como_confirmada(
        self,
        db: AsyncSession,
        prediccion_id: int,
        validada_por: int
    ) -> Optional[Prediccion]:
        """Marca predicción como confirmada."""
        prediccion = await self.get_by_id(db, prediccion_id)
        if not prediccion:
            return None
        
        prediccion.estado = EstadoPrediccion.CONFIRMADA.value
        prediccion.validada = True
        prediccion.validada_por = validada_por
        prediccion.validada_en = datetime.utcnow()
        
        await db.commit()
        await db.refresh(prediccion)
        return prediccion
    
    async def marcar_como_falsa(
        self,
        db: AsyncSession,
        prediccion_id: int,
        validada_por: int
    ) -> Optional[Prediccion]:
        """Marca predicción como falsa."""
        prediccion = await self.get_by_id(db, prediccion_id)
        if not prediccion:
            return None
        
        prediccion.estado = EstadoPrediccion.FALSA.value
        prediccion.validada = True
        prediccion.validada_por = validada_por
        prediccion.validada_en = datetime.utcnow()
        
        await db.commit()
        await db.refresh(prediccion)
        return prediccion
    
    async def count_by_moto(
        self,
        db: AsyncSession,
        moto_id: int,
        estado: Optional[str] = None
    ) -> int:
        """Cuenta predicciones de una moto."""
        query = select(func.count()).select_from(Prediccion).where(
            Prediccion.moto_id == moto_id
        )
        
        if estado:
            query = query.where(Prediccion.estado == estado)
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def get_estadisticas(
        self,
        db: AsyncSession,
        moto_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de predicciones."""
        query = select(Prediccion)
        
        if moto_id:
            query = query.where(Prediccion.moto_id == moto_id)
        if usuario_id:
            query = query.where(Prediccion.usuario_id == usuario_id)
        if fecha_desde:
            query = query.where(Prediccion.created_at >= fecha_desde)
        if fecha_hasta:
            query = query.where(Prediccion.created_at <= fecha_hasta)
        
        result = await db.execute(query)
        predicciones = list(result.scalars().all())
        
        total = len(predicciones)
        if total == 0:
            return {
                "total": 0,
                "confirmadas": 0,
                "falsas": 0,
                "pendientes": 0,
                "tasa_acierto": 0.0,
                "confianza_promedio": 0.0
            }
        
        confirmadas = sum(1 for p in predicciones if p.estado == EstadoPrediccion.CONFIRMADA.value)
        falsas = sum(1 for p in predicciones if p.estado == EstadoPrediccion.FALSA.value)
        pendientes = sum(1 for p in predicciones if p.estado == EstadoPrediccion.PENDIENTE.value)
        
        validadas = confirmadas + falsas
        tasa_acierto = confirmadas / validadas if validadas > 0 else 0.0
        
        confianza_promedio = sum(p.confianza for p in predicciones) / total
        
        return {
            "total": total,
            "confirmadas": confirmadas,
            "falsas": falsas,
            "pendientes": pendientes,
            "tasa_acierto": tasa_acierto,
            "confianza_promedio": confianza_promedio
        }


class EntrenamientoRepository:
    """Repositorio para entrenamientos de modelos."""
    
    async def create(
        self,
        db: AsyncSession,
        entrenamiento_data: Dict[str, Any]
    ) -> EntrenamientoModelo:
        """Crea un nuevo registro de entrenamiento."""
        entrenamiento = EntrenamientoModelo(**entrenamiento_data)
        db.add(entrenamiento)
        await db.commit()
        await db.refresh(entrenamiento)
        return entrenamiento
    
    async def get_by_id(
        self,
        db: AsyncSession,
        entrenamiento_id: int
    ) -> Optional[EntrenamientoModelo]:
        """Obtiene entrenamiento por ID."""
        result = await db.execute(
            select(EntrenamientoModelo).where(EntrenamientoModelo.id == entrenamiento_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_modelo(
        self,
        db: AsyncSession,
        nombre_modelo: str
    ) -> List[EntrenamientoModelo]:
        """Obtiene entrenamientos de un modelo."""
        result = await db.execute(
            select(EntrenamientoModelo)
            .where(EntrenamientoModelo.nombre_modelo == nombre_modelo)
            .order_by(desc(EntrenamientoModelo.created_at))
        )
        return list(result.scalars().all())
    
    async def get_en_produccion(
        self,
        db: AsyncSession,
        nombre_modelo: str
    ) -> Optional[EntrenamientoModelo]:
        """Obtiene modelo en producción."""
        result = await db.execute(
            select(EntrenamientoModelo).where(
                and_(
                    EntrenamientoModelo.nombre_modelo == nombre_modelo,
                    EntrenamientoModelo.en_produccion == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update(
        self,
        db: AsyncSession,
        entrenamiento: EntrenamientoModelo,
        update_data: Dict[str, Any]
    ) -> EntrenamientoModelo:
        """Actualiza un entrenamiento."""
        for key, value in update_data.items():
            setattr(entrenamiento, key, value)
        
        await db.commit()
        await db.refresh(entrenamiento)
        return entrenamiento
    
    async def marcar_produccion(
        self,
        db: AsyncSession,
        entrenamiento_id: int
    ) -> Optional[EntrenamientoModelo]:
        """Marca entrenamiento como en producción."""
        entrenamiento = await self.get_by_id(db, entrenamiento_id)
        if not entrenamiento:
            return None
        
        # Desmarcar otros modelos del mismo nombre
        await db.execute(
            select(EntrenamientoModelo)
            .where(
                and_(
                    EntrenamientoModelo.nombre_modelo == entrenamiento.nombre_modelo,
                    EntrenamientoModelo.en_produccion == True
                )
            )
        )
        
        entrenamiento.en_produccion = True
        await db.commit()
        await db.refresh(entrenamiento)
        return entrenamiento
