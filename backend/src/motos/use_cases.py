from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from .schemas import (
    MotoCreateSchema, MotoReadSchema, MotoUpdateSchema,
    EstadoActualSchema, DiagnosticoGeneralSchema, ModeloMotoSchema
)
from .repositories import MotoRepository, EstadoActualRepository, ModeloMotoRepository
from .services import MotoService
from .validators import validate_kilometraje, validate_kilometraje_no_disminuye
from src.shared.exceptions import NotFoundError, ValidationError, ForbiddenError

# Constantes para evitar literales duplicados
ERROR_MOTO_NOT_FOUND = "Moto no encontrada"
ERROR_MOTO_FORBIDDEN = "No tienes acceso a esta moto"
ERROR_MODELO_NOT_FOUND = "Modelo de moto no encontrado"


class CreateMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.modelo_repo = ModeloMotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, data: MotoCreateSchema, usuario_id: int) -> MotoReadSchema:
        # Validaciones de negocio adicionales (Pydantic ya validó formato)
        try:
            if data.kilometraje_actual:
                validate_kilometraje(Decimal(str(data.kilometraje_actual)))
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validar unicidad de VIN
        existing = await self.repo.get_by_vin(data.vin)
        if existing:
            raise ValidationError("Ya existe una moto con ese VIN")
        
        # Validar que el modelo existe
        modelo = await self.modelo_repo.get_by_id(data.modelo_moto_id)
        if not modelo:
            raise NotFoundError(ERROR_MODELO_NOT_FOUND)
        
        moto_data = self.service.prepare_moto_data(data.model_dump(), usuario_id)
        moto = await self.repo.create(moto_data)

        # 🔔 Crear notificación IN_APP al registrar la moto
                # 🔔 Crear notificación IN_APP al registrar la moto
        try:
            from src.notificaciones.repositories import (
                NotificacionRepository,
                PreferenciaNotificacionRepository,
            )
            from src.notificaciones.services import NotificacionService
            from src.notificaciones.use_cases import CrearNotificacionUseCase
            from src.notificaciones.models import TipoNotificacion, CanalNotificacion
            from src.shared.event_bus import event_bus

            notif_repo = NotificacionRepository(self.db)
            pref_repo = PreferenciaNotificacionRepository(self.db)
            notif_service = NotificacionService(notif_repo, pref_repo)
            crear_notif_uc = CrearNotificacionUseCase(notif_service, event_bus)

            # Kilometraje actual (0 si viene None)
            km_value = getattr(moto, "kilometraje_actual", None)
            if km_value is None:
                km_value = 0

            # Limpiar representación: 0.00 -> "0"
            if isinstance(km_value, (int, float, Decimal)):
                km_str = str(km_value).rstrip("0").rstrip(".")
            else:
                km_str = str(km_value)

            mensaje_km = (
                f"Tu moto con placa {moto.placa} ha sido registrada "
                f"con un kilometraje actual de {km_str} km."
            )

            await crear_notif_uc.execute(
                usuario_id=usuario_id,
                tipo=TipoNotificacion.INFO.value,
                titulo="Moto registrada",
                mensaje=mensaje_km,
                canal=CanalNotificacion.IN_APP.value,
                # ⚠️ referencia_tipo no acepta "moto", así que la dejamos en None
                # referencia_tipo=None y referencia_id=None son opcionales en el schema
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Error creando notificación de moto registrada: {e}"
            )


        # Provisionar estados iniciales para todos los componentes del modelo
        await self.service.provision_estados_iniciales(
            db=self.db,
            moto_id=moto.id,
            modelo_moto_id=moto.modelo_moto_id
        )
        
        # Nota: La provisión de sensores se hace desde el módulo 'sensores'
        # usando SensorTemplates cuando se llama al endpoint de provisión
        
        return MotoReadSchema.model_validate(moto)


class GetMotoUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MotoRepository(db)
        self.service = MotoService()
    
    async def execute(self, moto_id: int, usuario_id: int) -> MotoReadSchema:
        moto = await self.repo.get_by_id(moto_id)
        if not moto:
            raise NotFoundError(ERROR_MOTO_NOT_FOUND)
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError(ERROR_MOTO_FORBIDDEN)
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
            raise NotFoundError(ERROR_MOTO_NOT_FOUND)
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError(ERROR_MOTO_FORBIDDEN)
        
        update_data: Dict[str, Any] = data.model_dump(exclude_unset=True)
        
        # Validaciones de lógica de negocio (Pydantic ya validó formato)
        try:
            if "kilometraje_actual" in update_data:
                nuevo_km = Decimal(str(update_data["kilometraje_actual"]))
                validate_kilometraje(nuevo_km)
                # Regla de negocio: el kilometraje nunca puede disminuir
                validate_kilometraje_no_disminuye(nuevo_km, moto.kilometraje_actual)
                # Verificar si se debe emitir evento de servicio vencido
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
            raise NotFoundError(ERROR_MOTO_NOT_FOUND)
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError(ERROR_MOTO_FORBIDDEN)
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
            raise NotFoundError(ERROR_MOTO_NOT_FOUND)
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError(ERROR_MOTO_FORBIDDEN)
        
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
            raise NotFoundError(ERROR_MOTO_NOT_FOUND)
        if not self.service.verify_ownership(moto, usuario_id):
            raise ForbiddenError(ERROR_MOTO_FORBIDDEN)
        
        estados = await self.estado_repo.get_by_moto(moto_id)
        estado_general = self.service.calcular_estado_general(list(estados))
        
        # Convertir estados a schemas con información del componente
        estados_schemas = [
            EstadoActualSchema(
                id=e.id,  # PK actualizado: estado_actual_id → id
                moto_id=e.moto_id,
                componente_id=e.componente_id,
                componente_nombre=e.componente.nombre if e.componente else "Desconocido",
                ultimo_valor=e.ultimo_valor,  # Campo actualizado: valor_actual → ultimo_valor
                estado=e.estado,
                ultima_actualizacion=e.ultima_actualizacion
            )
            for e in estados
        ]
        
        # Obtener última actualización más reciente
        ultima_actualizacion = max(
            (e.ultima_actualizacion for e in estados),
            default=moto.updated_at
        )
        
        return DiagnosticoGeneralSchema(
            moto_id=moto_id,
            estado_general=estado_general,
            componentes=estados_schemas,
            ultima_actualizacion=ultima_actualizacion
        )


class ListModelosDisponiblesUseCase:
    """
    Lista los modelos de motos disponibles para registro.
    
    Usado en el flujo de onboarding cuando el usuario va a registrar su primera moto.
    Retorna solo los modelos activos (activo=true).
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ModeloMotoRepository(db)
    
    async def execute(self) -> List[ModeloMotoSchema]:
        """
        Ejecuta el caso de uso.
        
        Returns:
            List[ModeloMotoSchema]: Lista de modelos activos disponibles
        """
        modelos = await self.repo.list_activos()
        return [ModeloMotoSchema.model_validate(m) for m in modelos]
