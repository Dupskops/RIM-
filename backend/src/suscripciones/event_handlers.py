"""
Event handlers del módulo de suscripciones.
Escucha eventos de otros módulos y reacciona automáticamente.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.shared.event_bus import event_bus
from src.auth.events import UserRegisteredEvent
from .models import Suscripcion
from .repositories import SuscripcionRepository
from .services import SuscripcionService
from .events import emit_suscripcion_created
from src.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def handle_user_registered(event: UserRegisteredEvent) -> None:
    """
    Handler que escucha cuando un usuario se registra.
    Crea automáticamente una suscripción Freemium para el nuevo usuario.
    
    Args:
        event: Evento de usuario registrado
    """
    logger.info(
        f"📢 Evento recibido: Usuario registrado - "
        f"ID: {event.user_id}, Email: {event.email}"
    )
    
    try:
        # Convertir user_id de string a int (viene como string desde JWT)
        usuario_id = int(event.user_id)
        
        # Crear sesión de base de datos independiente
        async with AsyncSessionLocal() as session:
            repo = SuscripcionRepository(session)
            service = SuscripcionService()
            
            # Verificar que no tenga suscripción (por si acaso)
            existing = await repo.get_active_by_usuario(usuario_id)
            if existing:
                logger.warning(
                    f"⚠️ Usuario {usuario_id} ya tiene suscripción activa. "
                    f"No se crea suscripción Freemium."
                )
                return
            
            # Preparar datos de suscripción Freemium
            suscripcion_data = service.prepare_suscripcion_data(
                usuario_id=usuario_id,  # Ahora es int
                plan="freemium",
                duracion_meses=None,  # Freemium es indefinido
                precio=0.0,
                metodo_pago="none",
                transaction_id=None,
                auto_renovacion=False,
                notas=f"Suscripción Freemium creada automáticamente al registrar usuario {event.nombre}"
            )
            
            # Crear suscripción
            suscripcion = await repo.create(suscripcion_data)
            await session.commit()
            
            logger.info(
                f"✅ Suscripción Freemium creada automáticamente - "
                f"Usuario: {event.email}, Suscripción ID: {suscripcion.id}"
            )
            
            # Emitir evento de suscripción creada
            await emit_suscripcion_created(
                suscripcion_id=suscripcion.id,
                usuario_id=str(suscripcion.usuario_id),  # Convertir a string
                plan=suscripcion.plan,
                precio=float(suscripcion.precio) if suscripcion.precio else None
            )
            
    except Exception as e:
        logger.error(
            f"❌ Error al crear suscripción Freemium para usuario {event.user_id}: {e}",
            exc_info=True
        )
        # No lanzamos la excepción para no afectar el registro del usuario


def register_event_handlers():
    """
    Registra todos los event handlers de suscripciones.
    
    Esta función debe ser llamada al iniciar la aplicación (en main.py)
    para que los handlers queden suscritos a los eventos.
    """
    # Suscribir handler de usuario registrado
    event_bus.subscribe_async(UserRegisteredEvent, handle_user_registered)
    
    logger.info("✅ Event handlers de suscripciones registrados")
    logger.info("   - UserRegisteredEvent → handle_user_registered")
