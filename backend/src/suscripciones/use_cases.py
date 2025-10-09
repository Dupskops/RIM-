"""
Casos de uso del dominio de suscripciones.
"""
from datetime import datetime
from typing import Tuple, List
from fastapi import HTTPException, status

from .repositories import SuscripcionRepository
from .services import SuscripcionService
from .schemas import (
    CreateSuscripcionRequest,
    UpdateSuscripcionRequest,
    UpgradeToPremiumRequest,
    CancelSuscripcionRequest,
    RenewSuscripcionRequest,
    SuscripcionFilterParams,
    SuscripcionResponse,
    SuscripcionStatsResponse
)
from src.shared.base_models import PaginationParams
from .models import PlanType, SuscripcionStatus, Suscripcion
from .validators import calculate_end_date, validate_precio, validate_metodo_pago
from .events import (
    emit_suscripcion_created,
    emit_suscripcion_upgraded,
    emit_suscripcion_cancelled,
    emit_suscripcion_renewed,
    emit_suscripcion_updated
)


class CreateSuscripcionUseCase:
    """Caso de uso: Crear una nueva suscripción."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(self, request: CreateSuscripcionRequest) -> SuscripcionResponse:
        """
        Crea una nueva suscripción.
        
        Args:
            request: Datos de la suscripción
            
        Returns:
            Suscripción creada
            
        Raises:
            HTTPException: Si hay errores de validación
        """
        # Verificar que el usuario no tenga una suscripción activa
        existing = await self.repository.get_active_by_usuario(request.usuario_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya tiene una suscripción activa"
            )
        
        # Validar precio según plan
        is_valid, error_msg = validate_precio(request.precio, request.plan)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Validar método de pago según plan
        is_valid, error_msg = validate_metodo_pago(request.metodo_pago, request.plan)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Verificar transaction_id único (si se proporciona)
        if request.transaction_id:
            if await self.repository.transaction_exists(request.transaction_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El ID de transacción ya existe"
                )
        
        # Preparar datos
        suscripcion_data = self.service.prepare_suscripcion_data(
            usuario_id=request.usuario_id,
            plan=request.plan,
            duracion_meses=request.duracion_meses,
            precio=request.precio,
            metodo_pago=request.metodo_pago,
            transaction_id=request.transaction_id,
            auto_renovacion=request.auto_renovacion,
            notas=request.notas
        )
        
        # Crear suscripción
        suscripcion = await self.repository.create(suscripcion_data)
        
        # Emitir evento
        await emit_suscripcion_created(
            suscripcion_id=suscripcion.id,
            usuario_id=str(suscripcion.usuario_id),  # Convertir a string para evento
            plan=suscripcion.plan,
            precio=float(suscripcion.precio) if suscripcion.precio else None
        )
        
        # Retornar respuesta
        suscripcion_dict = self.service.build_suscripcion_response(suscripcion)
        return SuscripcionResponse(**suscripcion_dict)


class GetSuscripcionUseCase:
    """Caso de uso: Obtener una suscripción por ID."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        suscripcion_id: int,
        usuario_id: int,  # INTEGER
        is_admin: bool = False
    ) -> SuscripcionResponse:
        """
        Obtiene una suscripción por ID.
        
        Args:
            suscripcion_id: ID de la suscripción
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Suscripción encontrada
            
        Raises:
            HTTPException: Si no se encuentra o no tiene permiso
        """
        suscripcion = await self.repository.get_by_id(suscripcion_id)
        
        if not suscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suscripción no encontrada"
            )
        
        # Verificar ownership (admins pueden ver todas)
        if not is_admin and suscripcion.usuario_id != usuario_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta suscripción"
            )
        
        suscripcion_dict = self.service.build_suscripcion_response(suscripcion)
        return SuscripcionResponse(**suscripcion_dict)


class GetActiveSuscripcionUseCase:
    """Caso de uso: Obtener suscripción activa del usuario."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(self, usuario_id: int) -> SuscripcionResponse:  # INTEGER
        """
        Obtiene la suscripción activa del usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Suscripción activa
            
        Raises:
            HTTPException: Si no tiene suscripción activa
        """
        suscripcion = await self.repository.get_active_by_usuario(usuario_id)
        
        if not suscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes una suscripción activa"
            )
        
        suscripcion_dict = self.service.build_suscripcion_response(suscripcion)
        return SuscripcionResponse(**suscripcion_dict)


class ListSuscripcionesUseCase:
    """Caso de uso: Listar suscripciones con filtros."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        filters: SuscripcionFilterParams,
        pagination: PaginationParams,
        usuario_id: int,  # INTEGER
        is_admin: bool = False
    ) -> Tuple[List[Suscripcion], int]:
        """
        Lista suscripciones con filtros y paginación.
        
        Args:
            filters: Filtros de búsqueda
            pagination: Parámetros de paginación
            usuario_id: ID del usuario solicitante
            is_admin: Si el usuario es admin
            
        Returns:
            Tupla con lista de suscripciones y total
        """
        # Si no es admin, solo puede ver sus suscripciones
        usuario_filter = filters.usuario_id if is_admin else usuario_id
        
        # Obtener suscripciones
        suscripciones = await self.repository.list_suscripciones(
            usuario_id=usuario_filter,
            plan=filters.plan,
            status=filters.status,
            activas_only=filters.activas_only,
            skip=pagination.offset,
            limit=pagination.limit,
            order_by=filters.order_by,
            order_direction=filters.order_direction
        )
        
        # Contar total
        total = await self.repository.count_suscripciones(
            usuario_id=usuario_filter,
            plan=filters.plan,
            status=filters.status,
            activas_only=filters.activas_only
        )
        
        return suscripciones, total


class UpgradeToPremiumUseCase:
    """Caso de uso: Upgrade de freemium a premium."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        usuario_id: int,  # INTEGER
        request: UpgradeToPremiumRequest
    ) -> SuscripcionResponse:
        """
        Realiza upgrade a premium.
        
        Args:
            usuario_id: ID del usuario
            request: Datos del upgrade
            
        Returns:
            Suscripción actualizada
            
        Raises:
            HTTPException: Si hay errores
        """
        # Obtener suscripción activa
        suscripcion = await self.repository.get_active_by_usuario(usuario_id)
        
        if not suscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes una suscripción activa"
            )
        
        # Verificar si puede hacer upgrade
        can_upgrade, error_msg = self.service.can_upgrade(suscripcion)
        if not can_upgrade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Verificar transaction_id único
        if await self.repository.transaction_exists(request.transaction_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID de transacción ya existe"
            )
        
        # Calcular nueva fecha de fin
        new_end_date = calculate_end_date(datetime.utcnow(), request.duracion_meses)
        
        # Actualizar suscripción
        old_plan = suscripcion.plan
        update_data = {
            "plan": PlanType.PREMIUM,
            "end_date": new_end_date,
            "precio": request.precio,
            "metodo_pago": request.metodo_pago.lower(),
            "transaction_id": request.transaction_id,
            "auto_renovacion": request.auto_renovacion
        }
        
        updated_suscripcion = await self.repository.update(suscripcion, update_data)
        
        # Emitir evento
        await emit_suscripcion_upgraded(
            suscripcion_id=updated_suscripcion.id,
            usuario_id=str(usuario_id),  # Convertir a string para evento
            old_plan=old_plan,
            new_plan=PlanType.PREMIUM,
            precio=request.precio,
            duracion_meses=request.duracion_meses
        )
        
        suscripcion_dict = self.service.build_suscripcion_response(updated_suscripcion)
        return SuscripcionResponse(**suscripcion_dict)


class CancelSuscripcionUseCase:
    """Caso de uso: Cancelar suscripción."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        usuario_id: int,  # INTEGER
        request: CancelSuscripcionRequest
    ) -> None:
        """
        Cancela la suscripción activa.
        
        Args:
            usuario_id: ID del usuario
            request: Datos de cancelación
            
        Raises:
            HTTPException: Si hay errores
        """
        # Obtener suscripción activa
        suscripcion = await self.repository.get_active_by_usuario(usuario_id)
        
        if not suscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes una suscripción activa"
            )
        
        # Verificar si puede cancelar
        can_cancel, error_msg = self.service.can_cancel(suscripcion)
        if not can_cancel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Cancelar
        update_data = {
            "status": SuscripcionStatus.CANCELLED,
            "cancelled_at": datetime.utcnow(),
            "notas": request.razon if request.razon else suscripcion.notas
        }
        
        await self.repository.update(suscripcion, update_data)
        
        # Emitir evento
        await emit_suscripcion_cancelled(
            suscripcion_id=suscripcion.id,
            usuario_id=str(usuario_id),  # Convertir a string para evento
            plan=suscripcion.plan,
            cancelled_by=str(usuario_id),  # Convertir a string para evento
            razon=request.razon
        )


class RenewSuscripcionUseCase:
    """Caso de uso: Renovar suscripción premium."""
    
    def __init__(self, repository: SuscripcionRepository, service: SuscripcionService):
        self.repository = repository
        self.service = service
    
    async def execute(
        self,
        usuario_id: int,  # INTEGER
        request: RenewSuscripcionRequest
    ) -> SuscripcionResponse:
        """
        Renueva suscripción premium.
        
        Args:
            usuario_id: ID del usuario
            request: Datos de renovación
            
        Returns:
            Suscripción renovada
            
        Raises:
            HTTPException: Si hay errores
        """
        # Obtener suscripción activa
        suscripcion = await self.repository.get_active_by_usuario(usuario_id)
        
        if not suscripcion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes una suscripción activa"
            )
        
        # Verificar si puede renovar
        can_renew, error_msg = self.service.can_renew(suscripcion)
        if not can_renew:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Verificar transaction_id único
        if await self.repository.transaction_exists(request.transaction_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID de transacción ya existe"
            )
        
        # Calcular nueva fecha de fin (desde la actual o desde ahora)
        if suscripcion.end_date and suscripcion.end_date > datetime.utcnow():
            base_date = suscripcion.end_date
        else:
            base_date = datetime.utcnow()
        new_end_date = calculate_end_date(base_date, request.duracion_meses)
        
        # Renovar
        update_data = {
            "end_date": new_end_date,
            "status": SuscripcionStatus.ACTIVE,
            "transaction_id": request.transaction_id
        }
        
        updated_suscripcion = await self.repository.update(suscripcion, update_data)
        
        # Emitir evento
        await emit_suscripcion_renewed(
            suscripcion_id=updated_suscripcion.id,
            usuario_id=str(usuario_id),  # Convertir a string para evento
            plan=suscripcion.plan,
            new_end_date=new_end_date,
            precio=request.precio
        )
        
        suscripcion_dict = self.service.build_suscripcion_response(updated_suscripcion)
        return SuscripcionResponse(**suscripcion_dict)


class GetSuscripcionStatsUseCase:
    """Caso de uso: Obtener estadísticas de suscripciones."""
    
    def __init__(self, repository: SuscripcionRepository):
        self.repository = repository
    
    async def execute(self) -> SuscripcionStatsResponse:
        """
        Obtiene estadísticas de suscripciones.
        
        Returns:
            Estadísticas de suscripciones
        """
        stats = await self.repository.get_stats()
        return SuscripcionStatsResponse(**stats)
