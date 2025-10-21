"""
Repositorios para sensores (acceso a datos).
"""
from typing import Optional, List
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from .models import Sensor, LecturaSensor, EstadoSensor


class SensorRepository:
    """Repositorio para gestionar sensores."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, sensor_data: dict) -> Sensor:
        """Crea un nuevo sensor."""
        sensor = Sensor(**sensor_data)
        self.session.add(sensor)
        await self.session.commit()
        await self.session.refresh(sensor)
        return sensor
    
    async def get_by_id(self, sensor_id: int) -> Optional[Sensor]:
        """Obtiene un sensor por ID."""
        query = select(Sensor).where(
            Sensor.id == sensor_id,
            Sensor.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_codigo(self, codigo: str) -> Optional[Sensor]:
        """Obtiene un sensor por código."""
        query = select(Sensor).where(
            Sensor.codigo == codigo,
            Sensor.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_moto(
        self,
        moto_id: int,
        tipo: Optional[str] = None,
        estado: Optional[str] = None
    ) -> List[Sensor]:
        """Lista sensores de una moto con filtros."""
        query = select(Sensor).where(
            Sensor.moto_id == moto_id,
            Sensor.deleted_at.is_(None)
        )
        
        if tipo:
            query = query.where(Sensor.tipo == tipo)
        
        if estado:
            query = query.where(Sensor.estado == estado)
        
        query = query.order_by(Sensor.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_sensores(
        self,
        moto_id: Optional[int] = None,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Sensor]:
        """Lista sensores con paginación y filtros."""
        query = select(Sensor).where(Sensor.deleted_at.is_(None))
        
        if moto_id:
            query = query.where(Sensor.moto_id == moto_id)
        
        if tipo:
            query = query.where(Sensor.tipo == tipo)
        
        if estado:
            query = query.where(Sensor.estado == estado)
        
        query = query.order_by(Sensor.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_sensores(
        self,
        moto_id: Optional[int] = None,
        tipo: Optional[str] = None,
        estado: Optional[str] = None
    ) -> int:
        """Cuenta sensores con filtros."""
        query = select(func.count(Sensor.id)).where(Sensor.deleted_at.is_(None))
        
        if moto_id:
            query = query.where(Sensor.moto_id == moto_id)
        
        if tipo:
            query = query.where(Sensor.tipo == tipo)
        
        if estado:
            query = query.where(Sensor.estado == estado)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def update(self, sensor: Sensor, update_data: dict) -> Sensor:
        """Actualiza un sensor."""
        for key, value in update_data.items():
            if hasattr(sensor, key) and value is not None:
                setattr(sensor, key, value)
        
        sensor.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(sensor)
        return sensor
    
    async def delete(self, sensor: Sensor) -> None:
        """Elimina (soft delete) un sensor."""
        sensor.deleted_at = datetime.utcnow()
        await self.session.commit()
    
    async def update_ultima_lectura(self, sensor_id: int) -> None:
        """Actualiza el timestamp de última lectura."""
        sensor = await self.get_by_id(sensor_id)
        if sensor:
            sensor.ultima_lectura = datetime.utcnow()
            await self.session.commit()
    
    async def get_stats(self, moto_id: Optional[int] = None) -> dict:
        """Obtiene estadísticas de sensores."""
        query = select(Sensor).where(Sensor.deleted_at.is_(None))
        
        if moto_id:
            query = query.where(Sensor.moto_id == moto_id)
        
        result = await self.session.execute(query)
        sensores = list(result.scalars().all())
        
        return {
            "total": len(sensores),
            "activos": sum(1 for s in sensores if s.estado == EstadoSensor.ACTIVE),
            "inactivos": sum(1 for s in sensores if s.estado == EstadoSensor.INACTIVE),
            "con_error": sum(1 for s in sensores if s.estado == EstadoSensor.ERROR),
            "en_mantenimiento": sum(1 for s in sensores if s.estado == EstadoSensor.MAINTENANCE)
        }


class LecturaSensorRepository:
    """Repositorio para gestionar lecturas de sensores."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, lectura_data: dict) -> LecturaSensor:
        """Crea una nueva lectura."""
        lectura = LecturaSensor(**lectura_data)
        self.session.add(lectura)
        await self.session.commit()
        await self.session.refresh(lectura)
        return lectura
    
    async def get_by_id(self, lectura_id: int) -> Optional[LecturaSensor]:
        """Obtiene una lectura por ID."""
        query = select(LecturaSensor).where(LecturaSensor.id == lectura_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_latest_by_sensor(self, sensor_id: int) -> Optional[LecturaSensor]:
        """Obtiene la última lectura de un sensor."""
        query = select(LecturaSensor).where(
            LecturaSensor.sensor_id == sensor_id
        ).order_by(LecturaSensor.timestamp_lectura.desc()).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_by_sensor(
        self,
        sensor_id: int,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        fuera_rango: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LecturaSensor]:
        """Lista lecturas de un sensor con filtros."""
        query = select(LecturaSensor).where(LecturaSensor.sensor_id == sensor_id)
        
        if fecha_inicio:
            query = query.where(LecturaSensor.timestamp_lectura >= fecha_inicio)
        
        if fecha_fin:
            query = query.where(LecturaSensor.timestamp_lectura <= fecha_fin)
        
        if fuera_rango is not None:
            query = query.where(LecturaSensor.fuera_rango == fuera_rango)
        
        query = query.order_by(LecturaSensor.timestamp_lectura.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_by_sensor(
        self,
        sensor_id: int,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        fuera_rango: Optional[bool] = None
    ) -> int:
        """Cuenta lecturas de un sensor."""
        query = select(func.count(LecturaSensor.id)).where(
            LecturaSensor.sensor_id == sensor_id
        )
        
        if fecha_inicio:
            query = query.where(LecturaSensor.timestamp_lectura >= fecha_inicio)
        
        if fecha_fin:
            query = query.where(LecturaSensor.timestamp_lectura <= fecha_fin)
        
        if fuera_rango is not None:
            query = query.where(LecturaSensor.fuera_rango == fuera_rango)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def get_recent_lecturas(
        self,
        moto_id: Optional[int] = None,
        limit: int = 10
    ) -> List[LecturaSensor]:
        """Obtiene las lecturas más recientes."""
        query = select(LecturaSensor).join(Sensor)
        
        if moto_id:
            query = query.where(Sensor.moto_id == moto_id)
        
        query = query.order_by(LecturaSensor.timestamp_lectura.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_today(self, moto_id: Optional[int] = None) -> int:
        """Cuenta lecturas de hoy."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = select(func.count(LecturaSensor.id)).where(
            LecturaSensor.timestamp_lectura >= today_start
        )
        
        if moto_id:
            query = query.join(Sensor).where(Sensor.moto_id == moto_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def count_alerts_today(self, moto_id: Optional[int] = None) -> int:
        """Cuenta alertas generadas hoy."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = select(func.count(LecturaSensor.id)).where(
            LecturaSensor.timestamp_lectura >= today_start,
            LecturaSensor.alerta_generada == True
        )
        
        if moto_id:
            query = query.join(Sensor).where(Sensor.moto_id == moto_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
