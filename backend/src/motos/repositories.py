"""
Repositorios para el módulo de motos.

Define las clases de acceso a datos (Data Access Layer) usando SQLAlchemy.
Cada repositorio maneja operaciones CRUD para una entidad específica.

Versión: v2.3 MVP
"""
from typing import Optional, Sequence, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import ModeloMoto, Moto, Componente, ReglaEstado, EstadoActual, EstadoSalud


# ============================================
# REPOSITORIOS PRINCIPALES
# ============================================

class ModeloMotoRepository:
    """
    Repositorio para gestión de modelos de motos (catálogo).
    
    Gestiona la tabla 'modelos_moto' que contiene el catálogo de modelos
    soportados (KTM 390 Duke 2024, etc.).
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, modelo_id: int) -> Optional[ModeloMoto]:
        """
        Obtiene un modelo de moto por su ID.
        
        Usado en: CreateMotoUseCase (validar modelo existe)
        """
        result = await self.session.execute(
            select(ModeloMoto).where(ModeloMoto.id == modelo_id)
        )
        return result.scalar_one_or_none()
    
    async def list_activos(self) -> Sequence[ModeloMoto]:
        """
        Lista todos los modelos activos disponibles para registro.
        
        Usado en: ListModelosDisponiblesUseCase (onboarding)
        """
        result = await self.session.execute(
            select(ModeloMoto)
            .where(ModeloMoto.activo == True)
            .order_by(ModeloMoto.marca, ModeloMoto.nombre)
        )
        return result.scalars().all()


class MotoRepository:
    """
    Repositorio para gestión de motos (instancias individuales).
    
    Gestiona la tabla 'motos' con operaciones CRUD completas.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, moto_data: Dict[str, Any]) -> Moto:
        """
        Crea una nueva moto.
        
        Usado en: CreateMotoUseCase
        """
        moto = Moto(**moto_data)
        self.session.add(moto)
        await self.session.flush()
        await self.session.refresh(moto)
        return moto
    
    async def get_by_id(self, moto_id: int, load_relations: bool = False) -> Optional[Moto]:
        """
        Obtiene una moto por su ID (PK actualizado: moto_id → id).
        
        Args:
            moto_id: ID de la moto
            load_relations: Si True, carga usuario y estados_actuales
            
        Usado en: Get, Update, Delete, GetEstadoActual, GetDiagnostico UseCase
        """
        query = select(Moto).where(Moto.id == moto_id)
        
        if load_relations:
            query = query.options(
                selectinload(Moto.usuario),
                selectinload(Moto.estados_actuales).selectinload(EstadoActual.componente)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_vin(self, vin: str) -> Optional[Moto]:
        """
        Obtiene una moto por su VIN (Vehicle Identification Number).
        
        Usado en: CreateMotoUseCase (validar unicidad VIN)
        """
        result = await self.session.execute(
            select(Moto).where(Moto.vin == vin)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        usuario_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Moto]:
        """
        Lista motos con paginación opcional.
        
        Args:
            usuario_id: Filtrar por dueño (None = todas)
            skip: Offset para paginación
            limit: Cantidad máxima de resultados
            
        Usado en: ListMotosUseCase
        """
        query = select(Moto)
        
        if usuario_id:
            query = query.where(Moto.usuario_id == usuario_id)
        
        query = query.order_by(desc(Moto.created_at)).offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, moto_id: int, update_data: Dict[str, Any]) -> Moto:
        """
        Actualiza una moto existente.
        
        Usado en: UpdateMotoUseCase
        """
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
        """
        Elimina una moto (soft delete recomendado en producción).
        
        Usado en: DeleteMotoUseCase
        """
        moto = await self.get_by_id(moto_id)
        if moto:
            await self.session.delete(moto)
            await self.session.flush()


class EstadoActualRepository:
    """
    Repositorio para gestión de estados actuales de componentes.
    
    Gestiona la tabla 'estado_actual' que mantiene el estado en tiempo real
    de cada componente de cada moto.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_moto(self, moto_id: int) -> Sequence[EstadoActual]:
        """
        Obtiene todos los estados actuales de una moto (11 componentes).
        
        Usado en: GetEstadoActualUseCase, GetDiagnosticoGeneralUseCase
        """
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
        """
        Obtiene el estado actual de un componente específico de una moto.
        
        Usado en: procesar_lectura_y_actualizar_estado (services.py)
        """
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
        """
        Crea o actualiza el estado actual de un componente (UPSERT).
        
        Usado en: procesar_lectura_y_actualizar_estado (services.py)
        """
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
    
    async def create_bulk(self, estados: List[Dict[str, Any]]) -> None:
        """
        Crea múltiples estados actuales en lote (provisión inicial).
        
        Usado en: provision_estados_iniciales (services.py)
        Crea 11 registros al registrar una moto nueva.
        """
        for estado_data in estados:
            estado = EstadoActual(**estado_data)
            self.session.add(estado)
        await self.session.flush()


class ComponenteRepository:
    """
    Repositorio para gestión de componentes (partes de la moto).
    
    Gestiona la tabla 'componentes' que define las partes monitoreadas
    de cada modelo (Motor, Frenos, Neumáticos, etc.).
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def list_by_modelo(self, modelo_moto_id: int) -> Sequence[Componente]:
        """
        Lista todos los componentes de un modelo específico (11 para KTM 390 Duke).
        
        Usado en: provision_estados_iniciales (services.py)
        """
        result = await self.session.execute(
            select(Componente)
            .where(Componente.modelo_moto_id == modelo_moto_id)
            .order_by(Componente.nombre)
        )
        return result.scalars().all()


class ReglaEstadoRepository:
    """
    Repositorio para gestión de reglas de evaluación de estado.
    
    Gestiona la tabla 'reglas_estado' que define los umbrales para evaluar
    si un componente está en estado BUENO, ATENCION o CRITICO.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_componente_parametro(
        self,
        componente_id: int,
        parametro_id: int
    ) -> Optional[ReglaEstado]:
        """
        Obtiene una regla específica por componente y parámetro.
        
        Ejemplo: Regla de temperatura para Motor
        - limite_critico: >= 115°C
        - limite_atencion: >= 105°C
        - limite_bueno: >= 90°C
        
        Usado en: procesar_lectura_y_actualizar_estado (services.py)
        """
        result = await self.session.execute(
            select(ReglaEstado).where(
                and_(
                    ReglaEstado.componente_id == componente_id,
                    ReglaEstado.parametro_id == parametro_id
                )
            )
        )
        return result.scalar_one_or_none()
