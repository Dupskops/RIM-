from typing import Optional, Sequence
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Moto, Componente, Parametro, ReglaEstado, HistorialLectura, EstadoActual, EstadoSalud


class MotoRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, moto_data: dict) -> Moto:
        moto = Moto(**moto_data)
        self.session.add(moto)
        await self.session.flush()
        await self.session.refresh(moto)
        return moto
    
    async def get_by_id(self, moto_id: int, load_relations: bool = False) -> Optional[Moto]:
        query = select(Moto).where(Moto.moto_id == moto_id)
        
        if load_relations:
            query = query.options(
                selectinload(Moto.usuario),
                selectinload(Moto.estado_actual).selectinload(EstadoActual.componente)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_vin(self, vin: str) -> Optional[Moto]:
        result = await self.session.execute(
            select(Moto).where(Moto.vin == vin)
        )
        return result.scalar_one_or_none()
    
    async def get_by_placa(self, placa: str) -> Optional[Moto]:
        result = await self.session.execute(
            select(Moto).where(Moto.placa == placa)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        usuario_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Moto]:
        query = select(Moto)
        
        if usuario_id:
            query = query.where(Moto.usuario_id == usuario_id)
        
        query = query.order_by(desc(Moto.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self, usuario_id: Optional[int] = None) -> int:
        query = select(func.count(Moto.moto_id))
        
        if usuario_id:
            query = query.where(Moto.usuario_id == usuario_id)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def update(self, moto_id: int, update_data: dict) -> Moto:
        moto = await self.get_by_id(moto_id)
        if not moto:
            raise ValueError("Moto not found")
        
        for key, value in update_data.items():
            if value is not None:
                setattr(moto, key, value)
        
        await self.session.flush()
        await self.session.refresh(moto)
        return moto
    
    async def delete(self, moto_id: int) -> None:
        moto = await self.get_by_id(moto_id)
        if moto:
            await self.session.delete(moto)
            await self.session.flush()


class EstadoActualRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_moto(self, moto_id: int) -> Sequence[EstadoActual]:
        result = await self.session.execute(
            select(EstadoActual)
            .options(selectinload(EstadoActual.componente))
            .where(EstadoActual.moto_id == moto_id)
        )
        return result.scalars().all()
    
    async def get_by_componente(
        self,
        moto_id: int,
        componente_id: int
    ) -> Optional[EstadoActual]:
        result = await self.session.execute(
            select(EstadoActual).where(
                and_(
                    EstadoActual.moto_id == moto_id,
                    EstadoActual.componente_id == componente_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def upsert_estado_actual(
        self,
        moto_id: int,
        componente_id: int,
        ultimo_valor: Decimal,
        estado: EstadoSalud
    ) -> EstadoActual:
        existing = await self.get_by_componente(moto_id, componente_id)
        
        if existing:
            existing.ultimo_valor = ultimo_valor
            existing.estado = estado
            existing.ultima_actualizacion = datetime.now()
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            new_estado = EstadoActual(
                moto_id=moto_id,
                componente_id=componente_id,
                ultimo_valor=ultimo_valor,
                estado=estado,
                ultima_actualizacion=datetime.now()
            )
            self.session.add(new_estado)
            await self.session.flush()
            await self.session.refresh(new_estado)
            return new_estado


class HistorialLecturaRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        moto_id: int,
        parametro_id: int,
        valor: Decimal,
        timestamp: datetime
    ) -> HistorialLectura:
        lectura = HistorialLectura(
            moto_id=moto_id,
            parametro_id=parametro_id,
            valor=valor,
            timestamp=timestamp
        )
        self.session.add(lectura)
        await self.session.flush()
        await self.session.refresh(lectura)
        return lectura
    
    async def get_lecturas_recientes(
        self,
        moto_id: int,
        parametro_id: Optional[int] = None,
        limit: int = 100
    ) -> Sequence[HistorialLectura]:
        query = select(HistorialLectura).where(HistorialLectura.moto_id == moto_id)
        
        if parametro_id:
            query = query.where(HistorialLectura.parametro_id == parametro_id)
        
        query = query.order_by(desc(HistorialLectura.timestamp)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class ComponenteRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, componente_id: int) -> Optional[Componente]:
        result = await self.session.execute(
            select(Componente).where(Componente.componente_id == componente_id)
        )
        return result.scalar_one_or_none()
    
    async def list(self) -> Sequence[Componente]:
        result = await self.session.execute(select(Componente))
        return result.scalars().all()


class ParametroRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, parametro_id: int) -> Optional[Parametro]:
        result = await self.session.execute(
            select(Parametro).where(Parametro.parametro_id == parametro_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_nombre(self, nombre: str) -> Optional[Parametro]:
        result = await self.session.execute(
            select(Parametro).where(Parametro.nombre == nombre)
        )
        return result.scalar_one_or_none()
    
    async def list(self) -> Sequence[Parametro]:
        result = await self.session.execute(select(Parametro))
        return result.scalars().all()


class ReglaEstadoRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_componente(self, componente_id: int) -> Sequence[ReglaEstado]:
        result = await self.session.execute(
            select(ReglaEstado)
            .options(selectinload(ReglaEstado.parametro))
            .where(ReglaEstado.componente_id == componente_id)
        )
        return result.scalars().all()
    
    async def get_by_componente_parametro(
        self,
        componente_id: int,
        parametro_id: int
    ) -> Optional[ReglaEstado]:
        result = await self.session.execute(
            select(ReglaEstado).where(
                and_(
                    ReglaEstado.componente_id == componente_id,
                    ReglaEstado.parametro_id == parametro_id
                )
            )
        )
        return result.scalar_one_or_none()
