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
        import logging
        logger = logging.getLogger(__name__)
        
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
        
        # NUEVO: Validar límite de motos según plan de suscripción (MULTI_BIKE)
        try:
            await self._validar_limite_multi_bike(usuario_id)
        except ValidationError:
            raise  # Re-lanzar el error de validación
        except Exception as e:
            logger.warning(f"Error al validar límite MULTI_BIKE para usuario {usuario_id}: {e}")
            # Continuar si falla la validación del límite (failsafe)
        
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
        
        # NUEVO: Crear mantenimientos programados iniciales
        try:
            await self._crear_mantenimientos_iniciales(
                moto.id,
                int(moto.kilometraje_actual) if moto.kilometraje_actual else 0
            )
            logger.info(f"Mantenimientos iniciales creados para moto {moto.id}")
        except Exception as e:
            logger.warning(f"Error al crear mantenimientos iniciales para moto {moto.id}: {e}")
            # No fallar el registro de la moto si falla la creación de mantenimientos
        
        # NUEVO: Provisionar sensores automáticamente
        try:
            await self._provision_sensores_iniciales(moto.id, modelo.nombre)
            logger.info(f"Sensores provisionados automáticamente para moto {moto.id}")
        except Exception as e:
            logger.warning(f"Error al provisionar sensores para moto {moto.id}: {e}")
            # No fallar el registro de la moto si falla la provisión de sensores
        
        # NUEVO: Emitir evento de moto registrada para enviar email de confirmación
        try:
            from src.motos.events import emit_moto_registered
            from src.auth.repositories import UsuarioRepository
            
            # Obtener datos del usuario para el email
            usuario_repo = UsuarioRepository(self.db)
            usuario = await usuario_repo.get_by_id(usuario_id)
            
            if usuario:
                await emit_moto_registered(
                    moto_id=moto.id,
                    usuario_id=usuario_id,
                    placa=moto.placa,
                    modelo=modelo.nombre,
                    email_usuario=usuario.email,
                    nombre_usuario=usuario.nombre
                )
                logger.info(f"Evento MotoRegisteredEvent emitido para moto {moto.id}")
        except Exception as e:
            logger.warning(f"Error al emitir evento de moto registrada: {e}")
            # No fallar el registro si falla el envío del email
        
        return MotoReadSchema.model_validate(moto)
    
    async def _validar_limite_multi_bike(self, usuario_id: int) -> None:
        """
        Valida si el usuario puede crear otra moto según su plan de suscripción.
        
        Plan Free: máximo 2 motos (MULTI_BIKE limite_free = 2)
        Plan Pro: motos ilimitadas (MULTI_BIKE limite_pro = NULL)
        
        Raises:
            ValidationError: Si el usuario ha alcanzado el límite de motos
        """
        from src.suscripciones.services import LimiteService
        
        # Verificar límite de la característica MULTI_BIKE
        limite_service = LimiteService(self.db)
        resultado = await limite_service.check_limite(usuario_id, 'MULTI_BIKE')
        
        if not resultado["puede_usar"]:
            # El usuario ha alcanzado el límite de motos
            limite = resultado.get("limite")
            if limite == 0:
                raise ValidationError(
                    "La característica de múltiples motos no está disponible en tu plan. "
                    "Actualiza a Pro para registrar motos."
                )
            else:
                raise ValidationError(
                    f"Has alcanzado el límite de {limite} motos en tu plan Free. "
                    "Actualiza a Pro para registrar motos ilimitadas."
                )
        
        # Si puede usar, contar motos actuales para registrar el uso después
        motos_actuales = await self.repo.count_by_usuario(usuario_id)
        
        # Si ya tiene motos y el límite no es ilimitado, verificar contra el límite
        if resultado["limite"] is not None and motos_actuales >= resultado["limite"]:
            raise ValidationError(
                f"Has alcanzado el límite de {resultado['limite']} motos en tu plan. "
                "Actualiza a Pro para registrar motos ilimitadas."
            )
    
    async def _provision_sensores_iniciales(self, moto_id: int, modelo_nombre: str) -> None:
        """
        Provisiona sensores automáticamente para una moto recién registrada.
        
        Llama al ProvisionSensorsUseCase del módulo de sensores.
        """
        from src.sensores.use_cases import ProvisionSensorsUseCase
        
        provision_use_case = ProvisionSensorsUseCase(self.db)
        result = await provision_use_case.execute(moto_id=moto_id)
        
        return result
    
    async def _crear_mantenimientos_iniciales(self, moto_id: int, kilometraje_actual: int) -> None:
        """
        Crea mantenimientos programados iniciales para una moto recién registrada.
        
        Llama a la función crear_mantenimientos_iniciales del módulo de mantenimiento.
        """
        from src.mantenimiento.services import crear_mantenimientos_iniciales
        
        mantenimientos = await crear_mantenimientos_iniciales(
            db=self.db,
            moto_id=moto_id,
            kilometraje_actual=kilometraje_actual
        )
        
        return mantenimientos


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
