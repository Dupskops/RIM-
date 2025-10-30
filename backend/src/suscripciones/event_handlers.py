"""
Event handlers del módulo de suscripciones.
Escucha eventos de otros módulos y reacciona automáticamente.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from sqlalchemy import select, func, desc

from src.shared.event_bus import event_bus
from src.auth.events import UserRegisteredEvent
from .models import Suscripcion, Plan
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

            # Verificar que no tenga suscripción activa ya creada (buscar la más reciente)
            stmt = select(Suscripcion).where(Suscripcion.usuario_id == usuario_id).order_by(desc(Suscripcion.id)).limit(1)
            res = await session.execute(stmt)
            existing = res.scalars().first()
            if existing:
                logger.warning(
                    f"⚠️ Usuario {usuario_id} ya tiene suscripción activa. No se crea suscripción Freemium."
                )
                return

            # Buscar el plan 'freemium' en la tabla de planes
            plan_stmt = select(Plan).where(func.lower(Plan.nombre_plan) == "freemium")
            plan_res = await session.execute(plan_stmt)
            plan = plan_res.scalars().first()
            if not plan:
                logger.warning(f"⚠️ No se encontró el plan 'freemium' en la base de datos. No se crea suscripción para usuario {usuario_id}.")
                return

            # Preparar datos de suscripción Freemium usando el objeto Plan (asigna plan_id)
            suscripcion_data = service.prepare_suscripcion_data(
                usuario_id=usuario_id,
                plan=plan,
                duracion_meses=None,  # Freemium es indefinido
                precio=plan.precio if getattr(plan, "precio", None) is not None else 0.0,
                metodo_pago="none",
                transaction_id=None,
                auto_renovacion=False,
                notas=f"Suscripción Freemium creada automáticamente al registrar usuario {getattr(event, 'nombre', '')}"
            )

            # Crear/Asignar la suscripción usando el repositorio (assign_plan_to_user) —
            # este método actualizará si ya existiera una suscripción o la creará.
            # plan.id debería existir porque encontramos el plan en la BD; convertir a int
            plan_id: int = int(getattr(plan, "id"))
            assigned = await repo.assign_plan_to_user(
                usuario_id=usuario_id,
                plan_id=plan_id,
                fecha_inicio=suscripcion_data.get("fecha_inicio"),
                fecha_fin=suscripcion_data.get("fecha_fin"),
            )

            sus_id = getattr(assigned, "id", None)
            logger.info(
                f"✅ Suscripción Freemium creada automáticamente - Usuario: {getattr(event, 'email', usuario_id)}, Suscripción ID: {sus_id}"
            )

            # Emitir evento de suscripción creada sólo si tenemos id
            if sus_id is not None:
                await emit_suscripcion_created(
                    suscripcion_id=int(sus_id),
                    usuario_id=str(getattr(assigned, "usuario_id", usuario_id)),
                    plan=getattr(plan, "nombre_plan", "freemium"),
                    precio=float(getattr(plan, "precio", 0.0)) if getattr(plan, "precio", None) is not None else None,
                )

    except Exception as e:
        logger.error(
            f"❌ Error al crear suscripción Freemium para usuario {getattr(event, 'user_id', event.user_id)}: {e}",
            exc_info=True,
        )
        # No lanzamos la excepción para no afectar el flujo de registro del usuario


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
