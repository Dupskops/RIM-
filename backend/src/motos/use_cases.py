"""
Casos de uso del dominio de motos.
"""
from typing import Optional, Tuple, List
from fastapi import HTTPException, status

from src.shared.base_models import PaginationParams
from .repositories import MotoRepository
from .services import MotoService
from .models import Moto
from .schemas import (
    RegisterMotoRequest,
    UpdateMotoRequest,
    UpdateKilometrajeRequest,
    MotoFilterParams,
    MotoResponse,
    MotoStatsResponse
)
from .events import (
    emit_moto_registered,
    emit_moto_updated,
    emit_moto_deleted,
    emit_kilometraje_updated
)

from .repositories import MotoRepository
from .services import MotoService
from .schemas import (
    MotoComponenteCreate,
    MotoComponenteUpdate,
    MotoComponenteRead
)
from uuid import UUID


class RegisterMotoUseCase:
    """Caso de uso: Registrar una nueva moto."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        request: RegisterMotoRequest,
        usuario_id: int
    ) -> MotoResponse:
        """
        Registra una nueva moto.
        
        Args:
            request: Datos de la moto
            usuario_id: ID del usuario propietario
            
        Returns:
            Moto registrada
            
        Raises:
            HTTPException: Si VIN o placa ya existen
        """
        # Verificar VIN único
        if await self.repository.vin_exists(request.vin):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El VIN {request.vin} ya está registrado"
            )
        
        # Verificar placa única (si se proporciona)
        if request.placa and await self.repository.placa_exists(request.placa):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La placa {request.placa} ya está registrada"
            )
        
        # Preparar datos
        moto_data = self.service.prepare_moto_data(
            request.model_dump(exclude_unset=True),
            usuario_id
        )
        
        # Crear moto
        moto = await self.repository.create(moto_data)
        
        # Emitir evento
        await emit_moto_registered(
            moto_id=moto.id,
            usuario_id=usuario_id,
            vin=moto.vin,
            modelo=moto.modelo,
            año=moto.año,
            placa=moto.placa
        )
        
        # Retornar respuesta
        moto_dict = self.service.build_moto_response(moto)
        return MotoResponse(**moto_dict)


class GetMotoUseCase:
    """Caso de uso: Obtener una moto por ID."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        moto_id: int,
        usuario_id: int,
        is_admin: bool = False
    ) -> MotoResponse:
        """
        Obtiene una moto por ID.
        
        Args:
            moto_id: ID de la moto
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Moto encontrada
            
        Raises:
            HTTPException: Si no se encuentra o no tiene permiso
        """
        moto = await self.repository.get_by_id(moto_id, load_usuario=True)
        
        if not moto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moto no encontrada"
            )
        
        # Verificar ownership (admins pueden ver todas)
        if not is_admin and not self.service.verify_ownership(moto, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta moto"
            )
        
        moto_dict = self.service.build_moto_response(moto)
        return MotoResponse(**moto_dict)


class ListMotosUseCase:
    """Caso de uso: Listar motos con filtros."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        filters: MotoFilterParams,
        pagination: PaginationParams,
        usuario_id: int,
        is_admin: bool = False
    ) -> Tuple[List[Moto], int]:
        """
        Lista motos con filtros y paginación.
        
        Args:
            filters: Filtros de búsqueda
            pagination: Parámetros de paginación
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Tupla con (lista de motos, total)
        """
        # Si no es admin, solo puede ver sus motos
        effective_usuario_id = filters.usuario_id if is_admin else usuario_id
        
        # Obtener motos
        motos = await self.repository.list_motos(
            usuario_id=effective_usuario_id,
            modelo=filters.modelo,
            año_desde=filters.año_desde,
            año_hasta=filters.año_hasta,
            vin=filters.vin,
            placa=filters.placa,
            skip=pagination.offset,
            limit=pagination.limit,
            order_by=filters.order_by,
            order_direction=filters.order_direction,
            load_usuario=is_admin  # Solo cargar usuario si es admin
        )
        
        # Contar total
        total = await self.repository.count_motos(
            usuario_id=effective_usuario_id,
            modelo=filters.modelo,
            año_desde=filters.año_desde,
            año_hasta=filters.año_hasta,
            vin=filters.vin,
            placa=filters.placa
        )
        
        return motos, total


class UpdateMotoUseCase:
    """Caso de uso: Actualizar una moto."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        moto_id: int,
        request: UpdateMotoRequest,
        usuario_id: int,
        is_admin: bool = False
    ) -> MotoResponse:
        """
        Actualiza una moto.
        
        Args:
            moto_id: ID de la moto
            request: Datos a actualizar
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Moto actualizada
            
        Raises:
            HTTPException: Si no se encuentra o no tiene permiso
        """
        moto = await self.repository.get_by_id(moto_id)
        
        if not moto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moto no encontrada"
            )
        
        # Verificar ownership (admins pueden editar todas)
        if not is_admin and not self.service.verify_ownership(moto, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar esta moto"
            )
        
        # Obtener datos a actualizar
        update_data = request.model_dump(exclude_unset=True)
        
        # Verificar placa única (si se está actualizando)
        if "placa" in update_data and update_data["placa"]:
            if await self.repository.placa_exists(update_data["placa"], exclude_id=moto_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La placa {update_data['placa']} ya está registrada"
                )
            update_data["placa"] = update_data["placa"].upper()
        
        # Validar kilometraje si se está actualizando
        if "kilometraje" in update_data:
            is_valid, error_msg = self.service.validate_kilometraje_update(
                moto.kilometraje,
                update_data["kilometraje"]
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        
        # Actualizar
        updated_moto = await self.repository.update(moto, update_data)
        
        # Emitir evento
        await emit_moto_updated(
            moto_id=moto_id,
            usuario_id=moto.usuario_id,
            updated_fields=list(update_data.keys()),
            updated_by=usuario_id
        )
        
        moto_dict = self.service.build_moto_response(updated_moto)
        return MotoResponse(**moto_dict)


class DeleteMotoUseCase:
    """Caso de uso: Eliminar una moto."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        moto_id: int,
        usuario_id: int,
        is_admin: bool = False
    ) -> None:
        """
        Elimina una moto (soft delete).
        
        Args:
            moto_id: ID de la moto
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Raises:
            HTTPException: Si no se encuentra o no tiene permiso
        """
        moto = await self.repository.get_by_id(moto_id)
        
        if not moto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moto no encontrada"
            )
        
        # Verificar ownership (admins pueden eliminar todas)
        if not is_admin and not self.service.verify_ownership(moto, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta moto"
            )
        
        # Eliminar (soft delete)
        await self.repository.delete(moto, soft=True)
        
        # Emitir evento
        await emit_moto_deleted(
            moto_id=moto_id,
            usuario_id=moto.usuario_id,
            vin=moto.vin,
            deleted_by=usuario_id
        )


class UpdateKilometrajeUseCase:
    """Caso de uso: Actualizar solo el kilometraje."""
    
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        moto_id: int,
        request: UpdateKilometrajeRequest,
        usuario_id: int,
        is_admin: bool = False
    ) -> MotoResponse:
        """
        Actualiza el kilometraje de una moto.
        
        Args:
            moto_id: ID de la moto
            request: Nuevo kilometraje
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Moto actualizada
            
        Raises:
            HTTPException: Si no se encuentra o no tiene permiso
        """
        moto = await self.repository.get_by_id(moto_id)
        
        if not moto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moto no encontrada"
            )
        
        # Verificar ownership (admins pueden editar todas)
        if not is_admin and not self.service.verify_ownership(moto, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar esta moto"
            )
        
        # Validar kilometraje
        is_valid, error_msg = self.service.validate_kilometraje_update(
            moto.kilometraje,
            request.kilometraje
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Guardar kilometraje anterior
        old_kilometraje = moto.kilometraje
        
        # Actualizar
        updated_moto = await self.repository.update(
            moto,
            {"kilometraje": request.kilometraje}
        )
        
        # Emitir evento específico
        await emit_kilometraje_updated(
            moto_id=moto_id,
            usuario_id=moto.usuario_id,
            old_kilometraje=old_kilometraje,
            new_kilometraje=request.kilometraje,
            updated_by=usuario_id
        )
        
        moto_dict = self.service.build_moto_response(updated_moto)
        return MotoResponse(**moto_dict)


class GetMotoStatsUseCase:
    """Caso de uso: Obtener estadísticas de motos."""
    
    def __init__(self, repository: MotoRepository):
        self.repository = repository
    
    async def execute(self) -> MotoStatsResponse:
        """
        Obtiene estadísticas de motos.
        
        Returns:
            Estadísticas de motos
        """
        stats = await self.repository.get_stats()
        return MotoStatsResponse(**stats)


# ---------------- MotoComponente UseCases ----------------
class CreateComponenteUseCase:
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service

    async def execute(self, moto_id: int, data: MotoComponenteCreate) -> MotoComponenteRead:
        componente_data = self.service.prepare_componente_data(data.model_dump(exclude_unset=True), moto_id)
        componente = await self.repository.create_componente(componente_data)
        return MotoComponenteRead.model_validate(self.service.build_componente_response(componente))


class GetComponenteUseCase:
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service

    async def execute(self, componente_id: UUID) -> MotoComponenteRead:
        componente = await self.repository.get_componente_by_id(componente_id)
        if not componente:
            from src.shared.exceptions import NotFoundError
            raise NotFoundError("Componente no encontrado")
        return MotoComponenteRead.model_validate(self.service.build_componente_response(componente))


class ListComponentesUseCase:
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service

    async def execute(self, moto_id: int) -> list[ MotoComponenteRead ]:
        componentes = await self.repository.list_componentes_by_moto(moto_id)
        return [MotoComponenteRead.model_validate(self.service.build_componente_response(c)) for c in componentes]


class UpdateComponenteUseCase:
    def __init__(self, repository: MotoRepository, service: MotoService):
        self.repository = repository
        self.service = service

    async def execute(self, componente_id: UUID, data: MotoComponenteUpdate) -> MotoComponenteRead:
        componente = await self.repository.get_componente_by_id(componente_id)
        if not componente:
            from src.shared.exceptions import NotFoundError
            raise NotFoundError("Componente no encontrado")
        updated = await self.repository.update_componente(componente, data.model_dump(exclude_unset=True))
        return MotoComponenteRead.model_validate(self.service.build_componente_response(updated))


class DeleteComponenteUseCase:
    def __init__(self, repository: MotoRepository):
        self.repository = repository

    async def execute(self, componente_id: UUID) -> None:
        componente = await self.repository.get_componente_by_id(componente_id)
        if not componente:
            from src.shared.exceptions import NotFoundError
            raise NotFoundError("Componente no encontrado")
        await self.repository.delete_componente(componente)
