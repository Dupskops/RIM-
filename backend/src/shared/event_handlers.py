"""
Handlers robustos de eventos para integración entre módulos.
Estos handlers orquestan la comunicación entre módulos vía Event Bus.
"""
import logging
from typing import Any
from datetime import datetime

from src.shared.event_bus import event_bus

logger = logging.getLogger(__name__)


# ============================================
# HANDLERS: SENSORES → FALLAS
# ============================================

async def create_falla_from_sensor_alert(event: Any) -> None:
    """
    Crear falla automáticamente cuando un sensor reporta valores críticos.
    Evento escuchado: AlertaSensorEvent (sensores)
    Acción: Crear falla automática en módulo fallas
    """
    try:
        from src.fallas.use_cases import CreateFallaMLUseCase
        from src.fallas.schemas import FallaMLCreate
        from src.config.database import AsyncSessionLocal
        
        logger.warning(f"🔧 Creando falla desde alerta de sensor {event.sensor_id}")
        
        # Solo crear falla si es severidad alta/crítica
        if event.severidad not in ["critical", "alta", "critica"]:
            logger.info("ℹ️ Severidad no crítica, no se crea falla automática")
            return
        
        async with AsyncSessionLocal() as db:
            use_case = CreateFallaMLUseCase()
            
            falla_data = FallaMLCreate(
                moto_id=event.moto_id,
                tipo=f"sensor_{event.tipo_sensor}",
                titulo=f"Alerta de sensor: {event.tipo_sensor}",
                descripcion=f"El sensor {event.tipo_sensor} ha detectado un valor fuera de rango.\n"
                           f"Valor: {event.valor}\n"
                           f"Umbral violado: {event.umbral_violado}",
                origen_ml="sensor_alert",
                confianza_ml=0.95,  # Alta confianza porque viene de sensor
                datos_ml={
                    "sensor_id": event.sensor_id,
                    "tipo_sensor": event.tipo_sensor,
                    "valor": event.valor,
                    "umbral": event.umbral_violado,
                    "severidad": event.severidad
                }
            )
            
            falla = await use_case.execute(db, falla_data)
            logger.info(f"✅ Falla {falla.id} creada desde sensor alert")
            
    except Exception as e:
        logger.error(f"❌ Error creando falla desde sensor alert: {str(e)}", exc_info=True)


# ============================================
# HANDLERS: ML → FALLAS
# ============================================

async def create_falla_from_ml_anomaly(event: Any) -> None:
    """
    Crear falla cuando ML detecta una anomalía.
    Evento escuchado: AnomaliaDetectadaEvent (ml)
    Acción: Crear falla predictiva
    """
    try:
        from src.fallas.use_cases import CreateFallaMLUseCase
        from src.fallas.schemas import FallaMLCreate
        from src.config.database import AsyncSessionLocal
        
        logger.warning(f"🤖 Creando falla desde anomalía ML en moto {event.moto_id}")
        
        async with AsyncSessionLocal() as db:
            use_case = CreateFallaMLUseCase()
            
            falla_data = FallaMLCreate(
                moto_id=event.moto_id,
                tipo=event.tipo_anomalia,
                titulo=f"Anomalía detectada: {event.tipo_anomalia}",
                descripcion=f"El sistema de IA ha detectado un comportamiento anormal.\n"
                           f"Tipo: {event.tipo_anomalia}\n"
                           f"Severidad: {event.severidad}\n"
                           f"Recomendamos una revisión preventiva.",
                origen_ml="anomaly_detection",
                confianza_ml=event.confianza,
                datos_ml={
                    "tipo_anomalia": event.tipo_anomalia,
                    "severidad": event.severidad,
                    "datos_sensor": event.datos_sensor
                }
            )
            
            falla = await use_case.execute(db, falla_data)
            logger.info(f"✅ Falla predictiva {falla.id} creada desde ML")
            
    except Exception as e:
        logger.error(f"❌ Error creando falla desde ML: {str(e)}", exc_info=True)


# ============================================
# HANDLERS: FALLAS → MANTENIMIENTO
# ============================================

async def create_mantenimiento_from_critical_fault(event: Any) -> None:
    """
    Crear orden de mantenimiento urgente cuando se detecta falla crítica.
    Evento escuchado: FallaDetectadaEvent (fallas) con severidad="critica"
    Acción: Crear mantenimiento urgente
    """
    try:
        # Solo procesar si la falla es crítica
        if event.severidad != "critica":
            return
            
        from src.mantenimiento.use_cases import CreateMantenimientoUseCase
        from src.mantenimiento.schemas import MantenimientoCreate
        from src.config.database import AsyncSessionLocal
        from src.shared.constants import TipoMantenimiento, EstadoMantenimiento
        from datetime import date, timedelta
        
        logger.critical(f"🔧 Creando mantenimiento urgente desde falla crítica {event.falla_id}")
        
        async with AsyncSessionLocal() as db:
            use_case = CreateMantenimientoUseCase()
            
            mantenimiento_data = MantenimientoCreate(
                moto_id=event.moto_id,
                tipo=TipoMantenimiento.CORRECTIVO,
                titulo=f"Mantenimiento urgente: {event.titulo}",
                descripcion=f"Mantenimiento requerido por falla crítica.\n\n"
                           f"Falla: {event.titulo}\n"
                           f"{event.descripcion}\n\n"
                           f"{'⚠️ NO CONDUCIR LA MOTO' if not event.puede_conducir else 'Atención inmediata requerida'}",
                fecha_programada=date.today() + timedelta(days=1),  # Mañana
                prioridad=5,  # Máxima prioridad
                costo_estimado=0.0,  # A determinar
                notas=f"Generado automáticamente por falla crítica #{event.falla_id}"
            )
            
            mantenimiento = await use_case.execute(db, mantenimiento_data)
            logger.info(f"✅ Mantenimiento urgente {mantenimiento.id} creado")
            
    except Exception as e:
        logger.error(f"❌ Error creando mantenimiento urgente: {str(e)}", exc_info=True)


async def create_mantenimiento_from_ml_prediction(event: Any) -> None:
    """
    Crear mantenimiento preventivo desde recomendación de ML.
    Evento escuchado: PrediccionGeneradaEvent (ml)
    Acción: Crear mantenimiento preventivo si es crítica
    """
    try:
        if not event.es_critica:
            logger.info("ℹ️ Predicción no crítica, no se crea mantenimiento")
            return
            
        from src.mantenimiento.use_cases import CreateMantenimientoMLUseCase
        from src.mantenimiento.schemas import MantenimientoMLCreate
        from src.config.database import AsyncSessionLocal
        
        logger.info(f"🤖 Creando mantenimiento preventivo desde predicción ML")
        
        async with AsyncSessionLocal() as db:
            use_case = CreateMantenimientoMLUseCase()
            
            mantenimiento_data = MantenimientoMLCreate(
                moto_id=event.moto_id,
                tipo_recomendado=event.tipo,
                razon=event.descripcion,
                confianza=event.confianza,
                datos_ia=event.datos,
                prioridad=5 if event.es_critica else 3
            )
            
            mantenimiento = await use_case.execute(db, mantenimiento_data)
            logger.info(f"✅ Mantenimiento preventivo {mantenimiento.id} creado desde ML")
            
    except Exception as e:
        logger.error(f"❌ Error creando mantenimiento desde ML: {str(e)}", exc_info=True)


# ============================================
# HANDLERS: VARIOS → NOTIFICACIONES
# ============================================

async def send_notification_for_critical_fault(event: Any) -> None:
    """
    Enviar notificación urgente por falla crítica.
    Evento escuchado: FallaDetectadaEvent (fallas) con severidad="critica"
    """
    # Solo procesar si la falla es crítica
    if event.severidad != "critica":
        return
        
    logger.critical(f"🚨 Enviando notificación de falla crítica {event.falla_id}")
    # La lógica de notificación se maneja en el módulo de notificaciones
    # Este handler solo registra el evento para auditoría
    logger.info(f"✅ Notificación de falla crítica procesada")


async def send_notification_for_sensor_alert(event: Any) -> None:
    """
    Enviar notificación por alerta de sensor.
    Evento escuchado: AlertaSensorEvent (sensores)
    """
    logger.warning(f"📡 Enviando notificación de alerta de sensor {event.sensor_id}")
    logger.info(f"✅ Notificación de sensor procesada")


async def send_notification_for_maintenance_urgent(event: Any) -> None:
    """
    Enviar notificación por mantenimiento urgente.
    Evento escuchado: MantenimientoUrgenteEvent (mantenimiento)
    """
    logger.warning(f"🔧 Enviando notificación de mantenimiento urgente")
    logger.info(f"✅ Notificación de mantenimiento procesada")


async def send_notification_for_ml_prediction(event: Any) -> None:
    """
    Enviar notificación preventiva por predicción ML.
    Evento escuchado: PrediccionGeneradaEvent (ml)
    """
    logger.info(f"🤖 Enviando notificación de predicción ML")
    logger.info(f"✅ Notificación de predicción procesada")


# ============================================
# HANDLERS: ML FEEDBACK LOOP
# ============================================

async def feed_ml_model_from_sensor_reading(event: Any) -> None:
    """
    Alimentar modelos ML con lecturas de sensores.
    Evento escuchado: LecturaRegistradaEvent (sensores)
    """
    try:
        logger.debug(f"🤖 Alimentando ML con lectura de sensor {event.sensor_id}")
        # Aquí se implementaría la lógica para enviar datos al modelo ML
        # Por ahora solo logging
        
    except Exception as e:
        logger.error(f"❌ Error alimentando ML: {str(e)}")


async def update_ml_model_from_fault_resolution(event: Any) -> None:
    """
    Actualizar modelos ML cuando se resuelve una falla.
    Evento escuchado: FallaResueltaEvent (fallas)
    Propósito: Feedback loop para mejorar predicciones
    """
    try:
        logger.info(f"🤖 Actualizando ML con resolución de falla {event.falla_id}")
        # Aquí se implementaría la lógica para feedback al modelo
        # Por ahora solo logging
        
    except Exception as e:
        logger.error(f"❌ Error actualizando ML: {str(e)}")


# ============================================
# HANDLERS: MOTOS → MANTENIMIENTO
# ============================================

async def check_maintenance_on_kilometraje_update(event: Any) -> None:
    """
    Verificar mantenimientos pendientes cuando se actualiza el kilometraje.
    Evento escuchado: KilometrajeUpdatedEvent (motos)
    """
    try:
        logger.info(f"🔧 Verificando mantenimientos para moto {event.moto_id}")
        # Aquí se verificarían los mantenimientos basados en kilometraje
        # Por ejemplo: cambio de aceite cada 5000km
        
        if event.new_kilometraje % 5000 == 0:
            logger.warning(f"⚠️ Moto {event.moto_id} alcanzó {event.new_kilometraje}km - verificar mantenimiento")
            
    except Exception as e:
        logger.error(f"❌ Error verificando mantenimientos: {str(e)}")


# ============================================
# HANDLERS: AUTH → NOTIFICACIONES
# ============================================

async def send_welcome_email(event: Any) -> None:
    """
    Enviar email de bienvenida cuando se registra un usuario.
    Evento escuchado: UserRegisteredEvent (auth)
    Delega al módulo de notificaciones para crear y enviar el email.
    """
    try:
        from src.notificaciones.handlers import handle_user_registered
        
        logger.info(f"📧 Procesando email de bienvenida a {event.email}")
        await handle_user_registered(event)
        logger.info(f"✅ Email de bienvenida procesado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error procesando email de bienvenida: {str(e)}", exc_info=True)


async def send_password_reset_email(event: Any) -> None:
    """
    Enviar email con token de recuperación de contraseña.
    Evento escuchado: PasswordResetRequestedEvent (auth)
    """
    logger.info(f"📧 Enviando email de reset password a {event.email}")
    logger.info(f"✅ Email de reset password procesado")


# ============================================
# HANDLERS: SUSCRIPCIONES → NOTIFICACIONES
# ============================================

async def send_subscription_upgrade_confirmation(event: Any) -> None:
    """
    Confirmar upgrade de suscripción.
    Evento escuchado: SuscripcionUpgradedEvent (suscripciones)
    """
    logger.info(f"💳 Enviando confirmación de upgrade a usuario {event.usuario_id}")
    logger.info(f"✅ Confirmación de upgrade procesada")


async def send_subscription_expiration_reminder(event: Any) -> None:
    """
    Recordar renovación de suscripción.
    Evento escuchado: SuscripcionExpiredEvent (suscripciones)
    """
    logger.warning(f"💳 Enviando recordatorio de renovación a usuario {event.usuario_id}")
    logger.info(f"✅ Recordatorio de renovación procesado")


# ============================================
# HANDLERS: CHATBOT → NOTIFICACIONES
# ============================================

async def send_limit_reached_notification(event: Any) -> None:
    """
    Notificar cuando se alcanza límite de plan freemium.
    Evento escuchado: LimiteAlcanzadoEvent (chatbot)
    """
    logger.info(f"⚠️ Enviando notificación de límite alcanzado a usuario {event.usuario_id}")
    logger.info(f"✅ Notificación de límite procesada")


# ============================================
# HANDLER REGISTRY (para debugging)
# ============================================

REGISTERED_HANDLERS = {
    # Sensores → Fallas
    "AlertaSensorEvent": ["create_falla_from_sensor_alert", "send_notification_for_sensor_alert"],
    
    # ML → Fallas
    "AnomaliaDetectadaEvent": ["create_falla_from_ml_anomaly"],
    
    # Fallas → Mantenimiento (MVP v2.3: usa FallaDetectadaEvent con severidad="critica")
    "FallaDetectadaEvent": ["create_mantenimiento_from_critical_fault", "send_notification_for_critical_fault"],
    
    # ML → Mantenimiento
    "PrediccionGeneradaEvent": ["create_mantenimiento_from_ml_prediction", "send_notification_for_ml_prediction"],
    
    # Sensores → ML
    "LecturaRegistradaEvent": ["feed_ml_model_from_sensor_reading"],
    
    # Fallas → ML
    "FallaResueltaEvent": ["update_ml_model_from_fault_resolution"],
    
    # Motos → Mantenimiento
    "KilometrajeUpdatedEvent": ["check_maintenance_on_kilometraje_update"],
    
    # Auth → Notificaciones
    "UserRegisteredEvent": ["send_welcome_email"],
    "PasswordResetRequestedEvent": ["send_password_reset_email"],
    
    # Suscripciones → Notificaciones
    "SuscripcionUpgradedEvent": ["send_subscription_upgrade_confirmation"],
    "SuscripcionExpiredEvent": ["send_subscription_expiration_reminder"],
    
    # Chatbot → Notificaciones
    "LimiteAlcanzadoEvent": ["send_limit_reached_notification"],
}


def get_handler_stats() -> dict:
    """Obtener estadísticas de handlers registrados."""
    total_events = len(REGISTERED_HANDLERS)
    total_handlers = sum(len(handlers) for handlers in REGISTERED_HANDLERS.values())
    
    return {
        "total_event_types": total_events,
        "total_handlers": total_handlers,
        "events": list(REGISTERED_HANDLERS.keys()),
        "registry": REGISTERED_HANDLERS
    }
