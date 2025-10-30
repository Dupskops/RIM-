from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
from .models import Moto, EstadoActual, Componente, Parametro, ReglaEstado, HistorialLectura
from .schemas import (
    MotoCreateSchema, MotoReadSchema, MotoUpdateSchema,
    EstadoActualSchema, DiagnosticoGeneralSchema
)
from .repositories import MotoRepository, EstadoActualRepository
from .services import MotoService
from .validators import validate_vin, validate_placa, validate_ano, validate_kilometraje
from src.shared.exceptions import NotFoundError, ValidationError, ForbiddenError


class CreateMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, data: MotoCreateSchema, usuario_id: int) -> MotoReadSchema:
        try:
            validate_vin(data.vin)
            validate_placa(data.placa)
            validate_ano(data.ano)
            if data.kilometraje_actual:
                validate_kilometraje(Decimal(str(data.kilometraje_actual)))
        except ValueError as e:
            raise ValidationError(str(e))
        
        existing = await self.repo.get_by_vin(data.vin)
        if existing:
            raise ValidationError("Ya existe una moto con ese VIN")
        
        moto_data = self.service.prepare_moto_data(data.model_dump(), usuario_id)
        moto = await self.repo.create(moto_data)
        return MotoReadSchema.model_validate(moto)


class GetMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, usuario_id: int) -> MotoReadSchema:
        moto = await self.repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError("Moto no encontrada")
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError("No tienes acceso a esta moto")
        return MotoReadSchema.model_validate(moto)


class ListMotosUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
    
    async def execute(self, usuario_id: int, skip: int = 0, limit: int = 100) -> List[MotoReadSchema]:
        motos = await self.repo.list(usuario_id=usuario_id, skip=skip, limit=limit)
        return [MotoReadSchema.model_validate(m) for m in motos]


class UpdateMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, data: MotoUpdateSchema, usuario_id: int) -> MotoReadSchema:
        moto = await self.repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError("Moto no encontrada")
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError("No tienes acceso a esta moto")
        
        update_data = data.model_dump(exclude_unset=True)
        
        try:
            if "placa" in update_data:
                validate_placa(update_data["placa"])
            if "ano" in update_data:
                validate_ano(update_data["ano"])
            if "kilometraje_actual" in update_data:
                validate_kilometraje(Decimal(str(update_data["kilometraje_actual"])))
                if update_data["kilometraje_actual"] < moto.kilometraje_actual:
                    raise ValidationError("El kilometraje no puede disminuir")
                await self.service.check_servicio_vencido(moto, moto.kilometraje_actual)
        except ValueError as e:
            raise ValidationError(str(e))
        
        if "placa" in update_data or "color" in update_data:
            prepared_data = self.service.prepare_moto_data(update_data, usuario_id)
        else:
            prepared_data = update_data
        
        updated_moto = await self.repo.update(moto_id, prepared_data)
        return MotoReadSchema.model_validate(updated_moto)


class DeleteMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, usuario_id: int) -> None:
        moto = await self.repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError("Moto no encontrada")
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError("No tienes acceso a esta moto")
        await self.repo.delete(moto_id)


class GetEstadoActualUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.moto_repo = MotoRepository(db)
        self.estado_repo = EstadoActualRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, usuario_id: int) -> List[EstadoActualSchema]:
        moto = await self.moto_repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError("Moto no encontrada")
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError("No tienes acceso a esta moto")
        
        estados = await self.estado_repo.get_by_moto(moto_id)
        return [EstadoActualSchema.model_validate(e) for e in estados]


class GetDiagnosticoGeneralUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.moto_repo = MotoRepository(db)
        self.estado_repo = EstadoActualRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, usuario_id: int) -> DiagnosticoGeneralSchema:
        moto = await self.moto_repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError("Moto no encontrada")
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError("No tienes acceso a esta moto")
        
        estados = await self.estado_repo.get_by_moto(moto_id)
        estado_general = self.service.calcular_estado_general(estados)
        
        partes_afectadas = [
            {
                "componente_id": e.componente_id,
                "nombre": e.componente.nombre if e.componente else "Desconocido",
                "estado": e.estado.value,
                "valor_actual": float(e.valor_actual),
                "ultima_actualizacion": e.ultima_actualizacion
            }
            for e in estados
            if e.estado.value != "EXCELENTE"
        ]
        
        return DiagnosticoGeneralSchema(
            estado_general=estado_general.value,
            partes_afectadas=partes_afectadas
        )
