"""
Event handlers para el módulo de suscripciones (v2.3 Freemium).
"""
import logging

from src.auth.events import UserRegisteredEvent
from src.config.database import AsyncSessionLocal
from src.shared.event_bus import event_bus

from .events import emit_suscripcion_created
from .repositories import PlanesRepository, SuscripcionRepository
from .services import SuscripcionService

logger = logging.getLogger(__name__)


async def handle_user_registered(event: UserRegisteredEvent) -> None:
    """
    Crea una suscripción FREE cuando un usuario se registra.
    
    Args:
        event: Evento de usuario registrado (from auth.events)
    """
    # Convertir user_id (string) a int
    try:
        usuario_id = int(event.user_id)
    except (ValueError, TypeError) as e:
        logger.error(f"[handle_user_registered] Error al convertir user_id '{event.user_id}' a int: {e}")
        return
    
    logger.info(f"[handle_user_registered] Creando suscripción FREE para usuario {usuario_id} ({event.email})")
    
    async with AsyncSessionLocal() as session:
        try:
            # Repositorios
            suscripcion_repo = SuscripcionRepository(session)
            planes_repo = PlanesRepository(session)
            
            # Servicios
            suscripcion_service = SuscripcionService(session)
            
            # 1. Verificar si el usuario ya tiene una suscripción
            existing = await suscripcion_repo.get_by_usuario_id(usuario_id)
            if existing:
                logger.info(f"[handle_user_registered] Usuario {usuario_id} ya tiene suscripción. ID: {existing.id}")
                return
            
            # 2. Obtener plan FREE desde la base de datos
            plan_free = await planes_repo.get_plan_by_nombre("FREE")
            if not plan_free:
                logger.error("[handle_user_registered] Plan FREE no encontrado en la base de datos. Verificar seed data.")
                raise ValueError("Plan FREE no encontrado. Ejecutar seed data.")
            
            # 3. Crear suscripción usando el servicio genérico
            suscripcion = await suscripcion_service.cambiar_plan(
                usuario_id=usuario_id,
                nuevo_plan_id=plan_free.id
            )
            
            await session.commit()
            
            logger.info(
                f"[handle_user_registered] Suscripción FREE creada exitosamente. "
                f"Usuario: {usuario_id}, Suscripción ID: {suscripcion.id}"
            )
            
            # 4. Emitir evento de suscripción creada
            await emit_suscripcion_created(
                suscripcion_id=suscripcion.id,
                usuario_id=usuario_id,
                plan_nombre=plan_free.nombre_plan,
                plan_id=plan_free.id,
            )
            
        except Exception as e:
            logger.error(
                f"[handle_user_registered] Error al crear suscripción para usuario {usuario_id}: {e}",
                exc_info=True
            )
            await session.rollback()
            raise


def register_event_handlers() -> None:
    """
    Registra los manejadores de eventos del módulo de suscripciones.
    """
    event_bus.subscribe_async(UserRegisteredEvent, handle_user_registered)
    logger.info("[register_event_handlers] Suscripciones: Manejadores de eventos registrados.")
