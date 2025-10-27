"""
Repositorios para acceso a datos del módulo de sensores.

Capa de acceso a datos con operaciones CRUD y consultas específicas:
- SensorTemplateRepository: CRUD de plantillas
- SensorRepository: Gestión de sensores instanciados
- MotoComponenteRepository: Gestión de componentes físicos
- LecturaRepository: Persistencia y consultas de telemetría

Incluye logging y manejo robusto de errores.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import SensorTemplate, Sensor, Lectura, SensorState
from ..motos.models import MotoComponente, ComponentState

logger = logging.getLogger(__name__)


# ============================================
# SENSOR TEMPLATE REPOSITORY
# ============================================

class SensorTemplateRepository:
    """Repositorio para plantillas de sensores."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, template_data: Dict[str, Any]) -> SensorTemplate:
        """Crear nueva plantilla de sensor."""
        template = SensorTemplate(**template_data)
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template

    async def get_by_id(self, template_id: UUID) -> Optional[SensorTemplate]:
        """Obtener plantilla por ID."""
        result = await self.session.execute(
            select(SensorTemplate).where(SensorTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_modelo(self, modelo: str) -> List[SensorTemplate]:
        """Obtener todas las plantillas para un modelo de moto."""
        result = await self.session.execute(
            select(SensorTemplate)
            .where(SensorTemplate.modelo == modelo)
            .order_by(SensorTemplate.name)
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        modelo: Optional[str] = None
    ) -> List[SensorTemplate]:
        """Listar plantillas con filtros opcionales."""
        query = select(SensorTemplate)
        
        if modelo:
            query = query.where(SensorTemplate.modelo == modelo)
        
        query = query.order_by(SensorTemplate.modelo, SensorTemplate.name)
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, modelo: Optional[str] = None) -> int:
        """Contar plantillas."""
        query = select(func.count(SensorTemplate.id))
        
        if modelo:
            query = query.where(SensorTemplate.modelo == modelo)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(self, template_id: UUID, update_data: Dict[str, Any]) -> Optional[SensorTemplate]:
        """Actualizar plantilla."""
        template = await self.get_by_id(template_id)
        if not template:
            return None
        
        for key, value in update_data.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        
        await self.session.flush()
        await self.session.refresh(template)
        return template

    async def delete(self, template_id: UUID) -> bool:
        """Eliminar plantilla."""
        result = await self.session.execute(
            delete(SensorTemplate).where(SensorTemplate.id == template_id)
        )
        return result.rowcount > 0


# ============================================
# MOTO COMPONENTE REPOSITORY
# ============================================

class MotoComponenteRepository:
    """Repositorio para componentes físicos de motos."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, componente_data: Dict[str, Any]) -> MotoComponente:
        """Crear nuevo componente."""
        componente = MotoComponente(**componente_data)
        self.session.add(componente)
        await self.session.flush()
        await self.session.refresh(componente)
        return componente

    async def get_by_id(self, componente_id: UUID) -> Optional[MotoComponente]:
        """Obtener componente por ID con sensores asociados."""
        result = await self.session.execute(
            select(MotoComponente)
            .options(selectinload(MotoComponente.sensores))
            .where(MotoComponente.id == componente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_moto(self, moto_id: int) -> List[MotoComponente]:
        """Obtener todos los componentes de una moto."""
        result = await self.session.execute(
            select(MotoComponente)
            .options(selectinload(MotoComponente.sensores))
            .where(MotoComponente.moto_id == moto_id)
            .order_by(MotoComponente.tipo, MotoComponente.nombre)
        )
        return list(result.scalars().all())

    async def update_state(
        self,
        componente_id: UUID,
        new_state: ComponentState,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Optional[MotoComponente]:
        """Actualizar estado de componente."""
        try:
            componente = await self.get_by_id(componente_id)
            if not componente:
                logger.warning(f"Componente {componente_id} no encontrado para actualización de estado")
                return None
            
            componente.component_state = new_state
            componente.last_updated = datetime.now(timezone.utc)
            
            if extra_data:
                componente.extra_data = extra_data
            
            await self.session.flush()
            await self.session.refresh(componente)
            logger.info(f"Estado de componente {componente_id} actualizado a {new_state.value}")
            return componente
            
        except SQLAlchemyError as e:
            logger.error(f"Error actualizando estado de componente {componente_id}: {e}")
            raise

    async def delete(self, componente_id: UUID) -> bool:
        """Eliminar componente."""
        result = await self.session.execute(
            delete(MotoComponente).where(MotoComponente.id == componente_id)
        )
        return result.rowcount > 0


# ============================================
# SENSOR REPOSITORY
# ============================================

class SensorRepository:
    """Repositorio para sensores instanciados."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, sensor_data: Dict[str, Any]) -> Sensor:
        """Crear nuevo sensor."""
        sensor = Sensor(**sensor_data)
        self.session.add(sensor)
        await self.session.flush()
        await self.session.refresh(sensor)
        return sensor

    async def get_by_id(self, sensor_id: UUID) -> Optional[Sensor]:
        """Obtener sensor por ID."""
        result = await self.session.execute(
            select(Sensor)
            .options(
                selectinload(Sensor.template),
                selectinload(Sensor.componente)
            )
            .where(Sensor.id == sensor_id)
        )
        return result.scalar_one_or_none()

    async def get_by_moto(self, moto_id: int) -> List[Sensor]:
        """Obtener todos los sensores de una moto."""
        result = await self.session.execute(
            select(Sensor)
            .options(
                selectinload(Sensor.template),
                selectinload(Sensor.componente)
            )
            .where(Sensor.moto_id == moto_id)
            .order_by(Sensor.tipo, Sensor.nombre)
        )
        return list(result.scalars().all())

    async def list_sensores(
        self,
        skip: int = 0,
        limit: int = 100,
        moto_id: Optional[int] = None,
        tipo: Optional[str] = None,
        sensor_state: Optional[SensorState] = None,
        componente_id: Optional[UUID] = None
    ) -> List[Sensor]:
        """Listar sensores con filtros."""
        query = select(Sensor).options(
            selectinload(Sensor.template),
            selectinload(Sensor.componente)
        )
        
        filters = []
        if moto_id is not None:
            filters.append(Sensor.moto_id == moto_id)
        if tipo:
            filters.append(Sensor.tipo == tipo)
        if sensor_state:
            filters.append(Sensor.sensor_state == sensor_state)
        if componente_id:
            filters.append(Sensor.componente_id == componente_id)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(Sensor.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_sensores(
        self,
        moto_id: Optional[int] = None,
        tipo: Optional[str] = None,
        sensor_state: Optional[SensorState] = None
    ) -> int:
        """Contar sensores con filtros."""
        query = select(func.count(Sensor.id))
        
        filters = []
        if moto_id is not None:
            filters.append(Sensor.moto_id == moto_id)
        if tipo:
            filters.append(Sensor.tipo == tipo)
        if sensor_state:
            filters.append(Sensor.sensor_state == sensor_state)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(self, sensor_id: UUID, update_data: Dict[str, Any]) -> Optional[Sensor]:
        """Actualizar sensor."""
        sensor = await self.get_by_id(sensor_id)
        if not sensor:
            return None
        
        for key, value in update_data.items():
            if value is not None and hasattr(sensor, key):
                setattr(sensor, key, value)
        
        await self.session.flush()
        await self.session.refresh(sensor)
        return sensor

    async def update_last_seen(
        self,
        sensor_id: UUID,
        last_value: Optional[Dict[str, Any]] = None
    ) -> Optional[Sensor]:
        """Actualizar timestamp y último valor de sensor."""
        try:
            sensor = await self.get_by_id(sensor_id)
            if not sensor:
                logger.warning(f"Sensor {sensor_id} no encontrado para actualizar last_seen")
                return None
            
            sensor.last_seen = datetime.now(timezone.utc)
            if last_value:
                sensor.last_value = last_value
            
            await self.session.flush()
            await self.session.refresh(sensor)
            logger.debug(f"Last seen actualizado para sensor {sensor_id}")
            return sensor
            
        except SQLAlchemyError as e:
            logger.error(f"Error actualizando last_seen de sensor {sensor_id}: {e}")
            raise

    async def delete(self, sensor_id: UUID) -> bool:
        """Eliminar sensor."""
        result = await self.session.execute(
            delete(Sensor).where(Sensor.id == sensor_id)
        )
        return result.rowcount > 0

    async def get_stats(self, moto_id: Optional[int] = None) -> Dict[str, int]:
        """Obtener estadísticas de sensores por estado."""
        query = select(
            Sensor.sensor_state,
            func.count(Sensor.id)
        ).group_by(Sensor.sensor_state)
        
        if moto_id is not None:
            query = query.where(Sensor.moto_id == moto_id)
        
        result = await self.session.execute(query)
        stats = {state.value: 0 for state in SensorState}
        
        for state, count in result:
            stats[state.value] = count
        
        stats["total"] = sum(stats.values())
        return stats


# ============================================
# LECTURA REPOSITORY
# ============================================

class LecturaRepository:
    """Repositorio para lecturas de telemetría."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, lectura_data: Dict[str, Any]) -> Lectura:
        """Crear nueva lectura."""
        lectura = Lectura(**lectura_data)
        self.session.add(lectura)
        await self.session.flush()
        await self.session.refresh(lectura)
        return lectura

    async def batch_insert_readings(self, lecturas_data: List[Dict[str, Any]]) -> int:
        """
        Insertar múltiples lecturas en batch.
        Optimizado para el worker que procesa lecturas en lotes.
        
        Returns:
            Número de lecturas insertadas
        """
        if not lecturas_data:
            return 0
        
        lecturas = [Lectura(**data) for data in lecturas_data]
        self.session.add_all(lecturas)
        await self.session.flush()
        
        return len(lecturas)

    async def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        """Obtener lectura por ID."""
        result = await self.session.execute(
            select(Lectura).where(Lectura.id == lectura_id)
        )
        return result.scalar_one_or_none()

    async def list_by_moto(
        self,
        moto_id: int,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Lectura]:
        """Listar lecturas de una moto con filtros temporales."""
        query = select(Lectura).where(Lectura.moto_id == moto_id)
        
        if start_date:
            query = query.where(Lectura.ts >= start_date)
        if end_date:
            query = query.where(Lectura.ts <= end_date)
        
        query = query.order_by(Lectura.ts.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_sensor(
        self,
        sensor_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Lectura]:
        """Listar lecturas de un sensor con filtros temporales."""
        query = select(Lectura).where(Lectura.sensor_id == sensor_id)
        
        if start_date:
            query = query.where(Lectura.ts >= start_date)
        if end_date:
            query = query.where(Lectura.ts <= end_date)
        
        query = query.order_by(Lectura.ts.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_component(
        self,
        component_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Lectura]:
        """Listar lecturas de un componente con filtros temporales."""
        query = select(Lectura).where(Lectura.component_id == component_id)
        
        if start_date:
            query = query.where(Lectura.ts >= start_date)
        if end_date:
            query = query.where(Lectura.ts <= end_date)
        
        query = query.order_by(Lectura.ts.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_moto(
        self,
        moto_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Contar lecturas de una moto."""
        query = select(func.count(Lectura.id)).where(Lectura.moto_id == moto_id)
        
        if start_date:
            query = query.where(Lectura.ts >= start_date)
        if end_date:
            query = query.where(Lectura.ts <= end_date)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_by_sensor(
        self,
        sensor_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Contar lecturas de un sensor."""
        query = select(func.count(Lectura.id)).where(Lectura.sensor_id == sensor_id)
        
        if start_date:
            query = query.where(Lectura.ts >= start_date)
        if end_date:
            query = query.where(Lectura.ts <= end_date)
        
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_latest_by_sensor(self, sensor_id: UUID, limit: int = 10) -> List[Lectura]:
        """Obtener las últimas N lecturas de un sensor."""
        result = await self.session.execute(
            select(Lectura)
            .where(Lectura.sensor_id == sensor_id)
            .order_by(Lectura.ts.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
