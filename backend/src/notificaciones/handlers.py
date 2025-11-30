"""
Handlers de eventos para el módulo de notificaciones.
Estos handlers se suscriben a eventos de otros módulos y crean notificaciones automáticamente.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.notificaciones.models import TipoNotificacion, CanalNotificacion
from src.notificaciones.use_cases import CrearNotificacionUseCase
from src.notificaciones.services import NotificacionService
from src.config.database import get_db

logger = logging.getLogger(__name__)


# ============================================
# HANDLERS DE AUTH
# ============================================

async def handle_user_registered(event) -> None:
    """
    Handler: Enviar email de bienvenida cuando un usuario se registra.
    Evento: UserRegisteredEvent
    """
    try:
        logger.info(f"📧 Enviando email de bienvenida a usuario {event.user_id}")
        
        # Obtener sesión de BD
        async for db in get_db():
            # Crear servicios y use case con dependencias
            from src.notificaciones.repositories import NotificacionRepository, PreferenciaNotificacionRepository
            from src.shared.event_bus import event_bus
            
            notif_repo = NotificacionRepository(db)
            pref_repo = PreferenciaNotificacionRepository(db)
            notif_service = NotificacionService(notif_repo, pref_repo)
            use_case = CrearNotificacionUseCase(notif_service, event_bus)
            
            # Crear notificación
            logger.info(f"DEBUG: TipoNotificacion.INFO.value = {TipoNotificacion.INFO.value}")
            logger.info(f"DEBUG: Passing tipo={TipoNotificacion.INFO.value} to use_case")
            
            notificacion = await use_case.execute(
                usuario_id=int(event.user_id),
                tipo=TipoNotificacion.INFO.value,
                titulo="¡Bienvenido a RIM!",
                mensaje=f"Hola {event.nombre}, gracias por registrarte en RIM - Sistema Inteligente de Moto. "
                        f"Tu cuenta ha sido creada exitosamente. Email: {event.email}",
                canal=CanalNotificacion.EMAIL.value
            )
            
            # Guardar el email temporalmente en el objeto para el servicio de envío
            notificacion.email_destino = event.email
            notificacion.nombre_usuario = event.nombre
            
            # Enviar el email inmediatamente
            await notif_service.enviar_notificacion(notificacion.id, notificacion_obj=notificacion)
            
            break
            
        logger.info(f"✅ Email de bienvenida enviado a {event.email}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando email de bienvenida: {str(e)}")


async def handle_password_reset_requested(event) -> None:
    """
    Handler: Enviar email con token de recuperación de contraseña.
    Evento: PasswordResetRequestedEvent
    """
    try:
        logger.info(f"📧 Enviando email de reset password a usuario {event.user_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=event.user_id,
                tipo=TipoNotificacion.INFORMACION,
                titulo="Recuperación de contraseña",
                mensaje=f"Has solicitado recuperar tu contraseña. "
                        f"Usa el siguiente código para restablecer tu contraseña.",
                canal=CanalNotificacion.EMAIL,
                metadata={
                    "email": event.email,
                    "reset_token": event.reset_token,
                    "expires_in": "1 hora"
                }
            )
            break
            
        logger.info(f"✅ Email de reset password enviado a {event.email}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando email de reset password: {str(e)}")


async def handle_password_changed(event) -> None:
    """
    Handler: Enviar alerta de seguridad cuando cambia la contraseña.
    Evento: PasswordChangedEvent
    """
    try:
        logger.info(f"📧 Enviando alerta de cambio de contraseña a usuario {event.user_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=event.user_id,
                tipo=TipoNotificacion.ALERTA,
                titulo="Contraseña cambiada",
                mensaje="Tu contraseña ha sido cambiada exitosamente. "
                        "Si no realizaste este cambio, contacta soporte inmediatamente.",
                canal=CanalNotificacion.EMAIL,
                metadata={
                    "email": event.email,
                    "timestamp": event.timestamp.isoformat()
                }
            )
            break
            
        logger.info(f"✅ Alerta de cambio de contraseña enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de cambio de contraseña: {str(e)}")


# ============================================
# HANDLERS DE FALLAS
# ============================================

async def handle_falla_critica(event) -> None:
    """
    Handler: Enviar alerta URGENTE cuando se detecta una falla crítica.
    Evento: FallaDetectadaEvent con severidad="critica"
    Canales: SMS + Push + Email (máxima prioridad)
    """
    try:
        # Solo procesar si es crítica
        if event.severidad != "critica":
            return
            
        logger.critical(f"🚨 FALLA CRÍTICA detectada en moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            # Enviar por MÚLTIPLES canales (crítico)
            for canal in [CanalNotificacion.PUSH, CanalNotificacion.EMAIL, CanalNotificacion.SMS]:
                await use_case.execute(
                    db=db,
                    usuario_id=event.usuario_id if hasattr(event, 'usuario_id') else None,
                    tipo=TipoNotificacion.CRITICA,
                    titulo=f"⚠️ FALLA CRÍTICA: {event.titulo}",
                    mensaje=f"{event.descripcion}\n\n"
                            f"{'❌ NO CONDUCIR' if not event.puede_conducir else '⚠️ Atención inmediata requerida'}\n"
                            f"Contacta con un taller inmediatamente.",
                    canal=canal,
                    metadata={
                        "falla_id": event.falla_id,
                        "moto_id": event.moto_id,
                        "tipo": event.tipo,
                        "puede_conducir": event.puede_conducir,
                        "prioridad": "MAXIMA"
                    }
                )
            break
            
        logger.info(f"✅ Alertas críticas enviadas para falla {event.falla_id}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando alertas de falla crítica: {str(e)}")


async def handle_falla_detectada(event) -> None:
    """
    Handler: Notificar cuando se detecta una falla (no crítica).
    Evento: FallaDetectadaEvent con severidad != "critica"
    """
    try:
        # No procesar críticas aquí (las maneja handle_falla_critica)
        if event.severidad == "critica":
            return
            
        logger.warning(f"⚠️ Falla detectada en moto {event.moto_id}: {event.tipo}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            # Determinar severidad del mensaje
            if event.severidad in ["alta", "critica"]:
                tipo = TipoNotificacion.ALERTA
                canales = [CanalNotificacion.PUSH, CanalNotificacion.EMAIL]
            else:
                tipo = TipoNotificacion.INFORMACION
                canales = [CanalNotificacion.PUSH]
            
            for canal in canales:
                await use_case.execute(
                    db=db,
                    usuario_id=event.usuario_id,
                    tipo=tipo,
                    titulo=f"Falla detectada: {event.titulo}",
                    mensaje=f"{event.descripcion}\n\n"
                            f"Severidad: {event.severidad.upper()}\n"
                            f"Origen: {event.origen_deteccion}",
                    canal=canal,
                    metadata={
                        "falla_id": event.falla_id,
                        "moto_id": event.moto_id,
                        "tipo": event.tipo,
                        "severidad": event.severidad,
                        "requiere_atencion": event.requiere_atencion_inmediata
                    }
                )
            break
            
        logger.info(f"✅ Notificación de falla enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación de falla: {str(e)}")


# ============================================
# HANDLERS DE SENSORES
# ============================================

async def handle_alerta_sensor(event) -> None:
    """
    Handler: Notificar cuando un sensor reporta valores fuera de rango.
    Evento: AlertaSensorEvent
    """
    try:
        logger.warning(f"⚠️ Alerta de sensor {event.tipo_sensor} en moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            # Determinar urgencia
            es_critica = event.severidad in ["critical", "alta", "critica"]
            tipo = TipoNotificacion.CRITICA if es_critica else TipoNotificacion.ALERTA
            canales = [CanalNotificacion.PUSH, CanalNotificacion.EMAIL] if es_critica else [CanalNotificacion.PUSH]
            
            for canal in canales:
                await use_case.execute(
                    db=db,
                    usuario_id=None,  # Se obtiene de moto_id
                    tipo=tipo,
                    titulo=f"⚠️ Alerta de sensor: {event.tipo_sensor}",
                    mensaje=f"El sensor {event.tipo_sensor} ha detectado un valor anormal.\n\n"
                            f"Valor actual: {event.valor}\n"
                            f"Umbral violado: {event.umbral_violado}\n"
                            f"Severidad: {event.severidad}",
                    canal=canal,
                    metadata={
                        "sensor_id": event.sensor_id,
                        "moto_id": event.moto_id,
                        "tipo_sensor": event.tipo_sensor,
                        "valor": event.valor,
                        "umbral": event.umbral_violado,
                        "severidad": event.severidad
                    }
                )
            break
            
        logger.info(f"✅ Alerta de sensor enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de sensor: {str(e)}")


# ============================================
# HANDLERS DE MANTENIMIENTO
# ============================================

async def handle_mantenimiento_urgente(event) -> None:
    """
    Handler: Notificar mantenimiento urgente.
    Evento: MantenimientoUrgenteEvent
    """
    try:
        logger.warning(f"🔧 Mantenimiento urgente para moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=None,  # Se obtiene de moto_id
                tipo=TipoNotificacion.ALERTA,
                titulo=f"🔧 Mantenimiento urgente requerido",
                mensaje=f"Tu moto requiere mantenimiento urgente.\n\n"
                        f"Tipo: {event.tipo}\n"
                        f"Motivo: {event.motivo_urgencia}\n"
                        f"Prioridad: {'⚠️ ALTA' if event.prioridad >= 4 else 'Media'}",
                canal=CanalNotificacion.PUSH,
                metadata={
                    "mantenimiento_id": event.mantenimiento_id,
                    "moto_id": event.moto_id,
                    "tipo": event.tipo,
                    "prioridad": event.prioridad
                }
            )
            break
            
        logger.info(f"✅ Alerta de mantenimiento urgente enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando alerta de mantenimiento urgente: {str(e)}")


async def handle_mantenimiento_vencido(event) -> None:
    """
    Handler: Recordar mantenimiento vencido.
    Evento: MantenimientoVencidoEvent
    """
    try:
        logger.warning(f"📅 Mantenimiento vencido para moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=None,  # Se obtiene de moto_id
                tipo=TipoNotificacion.RECORDATORIO,
                titulo=f"📅 Mantenimiento vencido",
                mensaje=f"Tu mantenimiento está vencido hace {event.dias_vencido} días.\n\n"
                        f"Tipo: {event.tipo}\n"
                        f"{event.descripcion}\n\n"
                        f"Agenda tu cita lo antes posible.",
                canal=CanalNotificacion.EMAIL,
                metadata={
                    "mantenimiento_id": event.mantenimiento_id,
                    "moto_id": event.moto_id,
                    "dias_vencido": event.dias_vencido
                }
            )
            break
            
        logger.info(f"✅ Recordatorio de mantenimiento vencido enviado")
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorio de mantenimiento: {str(e)}")


async def handle_mantenimiento_proximo(event) -> None:
    """
    Handler: Recordar mantenimiento próximo.
    Evento: AlertaMantenimientoProximoEvent
    """
    try:
        logger.info(f"📅 Mantenimiento próximo para moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=None,  # Se obtiene de moto_id
                tipo=TipoNotificacion.RECORDATORIO,
                titulo=f"📅 Mantenimiento próximo",
                mensaje=f"Tu mantenimiento está próximo (en {event.dias_restantes} días).\n\n"
                        f"Tipo: {event.tipo}\n"
                        f"Programa tu cita con anticipación.",
                canal=CanalNotificacion.PUSH,
                metadata={
                    "mantenimiento_id": event.mantenimiento_id,
                    "moto_id": event.moto_id,
                    "dias_restantes": event.dias_restantes
                }
            )
            break
            
        logger.info(f"✅ Recordatorio de mantenimiento próximo enviado")
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorio de mantenimiento: {str(e)}")


# ============================================
# HANDLERS DE ML
# ============================================

async def handle_prediccion_generada(event) -> None:
    """
    Handler: Notificar predicción de ML (preventiva).
    Evento: PrediccionGeneradaEvent
    """
    try:
        logger.info(f"🤖 Predicción generada para moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            # Si es crítica, mayor urgencia
            tipo = TipoNotificacion.ALERTA if event.es_critica else TipoNotificacion.INFORMACION
            canal = CanalNotificacion.PUSH if event.es_critica else CanalNotificacion.PUSH
            
            await use_case.execute(
                db=db,
                usuario_id=event.usuario_id,
                tipo=tipo,
                titulo=f"🤖 {'⚠️ ' if event.es_critica else ''}Predicción: {event.tipo}",
                mensaje=f"{event.descripcion}\n\n"
                        f"Confianza: {event.confianza * 100:.1f}%\n"
                        f"{'Recomendamos atención inmediata.' if event.es_critica else 'Recomendación preventiva.'}",
                canal=canal,
                metadata={
                    "prediccion_id": event.prediccion_id,
                    "moto_id": event.moto_id,
                    "tipo": event.tipo,
                    "confianza": event.confianza,
                    "es_critica": event.es_critica
                }
            )
            break
            
        logger.info(f"✅ Notificación de predicción enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación de predicción: {str(e)}")


async def handle_anomalia_detectada(event) -> None:
    """
    Handler: Notificar anomalía detectada por ML.
    Evento: AnomaliaDetectadaEvent
    """
    try:
        logger.warning(f"🤖 Anomalía detectada en moto {event.moto_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            tipo = TipoNotificacion.ALERTA if event.severidad in ["alta", "critica"] else TipoNotificacion.INFORMACION
            
            await use_case.execute(
                db=db,
                usuario_id=None,  # Se obtiene de moto_id
                tipo=tipo,
                titulo=f"🤖 Anomalía detectada: {event.tipo_anomalia}",
                mensaje=f"Se ha detectado un comportamiento anormal en tu moto.\n\n"
                        f"Tipo: {event.tipo_anomalia}\n"
                        f"Severidad: {event.severidad}\n"
                        f"Confianza: {event.confianza * 100:.1f}%\n\n"
                        f"Recomendamos una revisión.",
                canal=CanalNotificacion.PUSH,
                metadata={
                    "moto_id": event.moto_id,
                    "tipo_anomalia": event.tipo_anomalia,
                    "severidad": event.severidad,
                    "confianza": event.confianza,
                    "datos_sensor": event.datos_sensor
                }
            )
            break
            
        logger.info(f"✅ Notificación de anomalía enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación de anomalía: {str(e)}")


# ============================================
# HANDLERS DE SUSCRIPCIONES
# ============================================

async def handle_suscripcion_upgraded(event) -> None:
    """
    Handler: Confirmar upgrade a premium.
    Evento: SuscripcionUpgradedEvent
    """
    try:
        logger.info(f"💳 Suscripción upgraded para usuario {event.usuario_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=event.usuario_id,
                tipo=TipoNotificacion.INFORMACION,
                titulo=f"✨ ¡Bienvenido a {event.new_plan.upper()}!",
                mensaje=f"Tu suscripción ha sido actualizada exitosamente.\n\n"
                        f"Plan anterior: {event.old_plan}\n"
                        f"Nuevo plan: {event.new_plan}\n"
                        f"Precio: ${event.precio}\n"
                        f"Duración: {event.duracion_meses} meses\n\n"
                        f"¡Disfruta de todas las funciones premium!",
                canal=CanalNotificacion.EMAIL,
                metadata={
                    "suscripcion_id": event.suscripcion_id,
                    "old_plan": event.old_plan,
                    "new_plan": event.new_plan,
                    "precio": event.precio
                }
            )
            break
            
        logger.info(f"✅ Confirmación de upgrade enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando confirmación de upgrade: {str(e)}")


async def handle_suscripcion_expired(event) -> None:
    """
    Handler: Recordar renovación de suscripción.
    Evento: SuscripcionExpiredEvent
    """
    try:
        logger.warning(f"💳 Suscripción expirada para usuario {event.usuario_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=event.usuario_id,
                tipo=TipoNotificacion.RECORDATORIO,
                titulo=f"💳 Tu suscripción {event.plan} ha expirado",
                mensaje=f"Tu suscripción ha expirado. Renueva ahora para seguir disfrutando de todas las funciones.\n\n"
                        f"Plan: {event.plan}\n"
                        f"Renueva desde la app.",
                canal=CanalNotificacion.EMAIL,
                metadata={
                    "suscripcion_id": event.suscripcion_id,
                    "plan": event.plan
                }
            )
            break
            
        logger.info(f"✅ Recordatorio de renovación enviado")
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorio de renovación: {str(e)}")


# ============================================
# HANDLERS DE CHATBOT
# ============================================

async def handle_limite_alcanzado(event) -> None:
    """
    Handler: Notificar cuando se alcanza límite de plan freemium.
    Evento: LimiteAlcanzadoEvent
    """
    try:
        logger.info(f"⚠️ Límite alcanzado para usuario {event.usuario_id}")
        
        async for db in get_db():
            use_case = CrearNotificacionUseCase()
            
            await use_case.execute(
                db=db,
                usuario_id=event.usuario_id,
                tipo=TipoNotificacion.INFORMACION,
                titulo=f"Límite de {event.limite_tipo} alcanzado",
                mensaje=f"Has alcanzado el límite de tu plan {event.plan}.\n\n"
                        f"Límite: {event.limite_valor} {event.limite_tipo}\n"
                        f"Actualiza a Premium para disfrutar de acceso ilimitado.",
                canal=CanalNotificacion.PUSH,
                metadata={
                    "plan": event.plan,
                    "limite_tipo": event.limite_tipo,
                    "limite_valor": event.limite_valor
                }
            )
            break
            
        logger.info(f"✅ Notificación de límite enviada")
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación de límite: {str(e)}")
