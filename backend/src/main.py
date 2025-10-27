"""
RIM - Sistema Inteligente de Moto con IA
Punto de entrada principal de la aplicación.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from .config.settings import settings
from .config.database import init_db, close_db, check_db_connection
from .shared.event_bus import event_bus
from .integraciones.llm_provider import get_llm_provider

# Configure logging early using central config
from .config.logging import configure_logging

configure_logging(settings)

# Importar routers de todos los módulos
from .auth import auth_router
from .usuarios import usuarios_router
from .motos import motos_router
from .suscripciones import suscripciones_router
from .sensores import sensores_router, websocket_router
from .fallas import fallas_router
from .mantenimiento import mantenimiento_router
from .chatbot import chatbot_router
from .notificaciones import notificaciones_router
from .ml import ml_router

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN DE EVENT HANDLERS
# ============================================
async def setup_event_handlers():
    """
    Registrar todos los handlers de eventos para comunicación entre módulos.
    Este es el punto central donde se configura el Event Bus.
    """
    from .shared import event_handlers as handlers
    
    # Importar clases de eventos
    from .sensores.events import AlertaSensorEvent, LecturaRegistradaEvent
    from .fallas.events import FallaCriticaEvent, FallaResueltaEvent
    from .mantenimiento.events import (
        MantenimientoUrgenteEvent, 
    )
    from .ml.events import PrediccionGeneradaEvent, AnomaliaDetectadaEvent
    from .motos.events import KilometrajeUpdatedEvent
    from .auth.events import UserRegisteredEvent, PasswordResetRequestedEvent
    from .suscripciones.events import SuscripcionUpgradedEvent, SuscripcionExpiredEvent
    from .chatbot.events import LimiteAlcanzadoEvent
    
    logger.info("📡 Registrando event handlers...")
    
    # ========================================
    # SENSORES → FALLAS (Detección automática)
    # ========================================
    event_bus.subscribe_async(AlertaSensorEvent, handlers.create_falla_from_sensor_alert)
    event_bus.subscribe_async(AlertaSensorEvent, handlers.send_notification_for_sensor_alert)
    logger.info("✅ Sensores → Fallas (2 handlers)")
    
    # ========================================
    # ML → FALLAS (Detección predictiva)
    # ========================================
    event_bus.subscribe_async(AnomaliaDetectadaEvent, handlers.create_falla_from_ml_anomaly)
    logger.info("✅ ML → Fallas (1 handler)")
    
    # ========================================
    # FALLAS → MANTENIMIENTO (Auto-creación)
    # ========================================
    event_bus.subscribe_async(FallaCriticaEvent, handlers.create_mantenimiento_from_critical_fault)
    event_bus.subscribe_async(FallaCriticaEvent, handlers.send_notification_for_critical_fault)
    logger.info("✅ Fallas → Mantenimiento (2 handlers)")
    
    # ========================================
    # ML → MANTENIMIENTO (Predictivo)
    # ========================================
    event_bus.subscribe_async(PrediccionGeneradaEvent, handlers.create_mantenimiento_from_ml_prediction)
    event_bus.subscribe_async(PrediccionGeneradaEvent, handlers.send_notification_for_ml_prediction)
    logger.info("✅ ML → Mantenimiento (2 handlers)")
    
    # ========================================
    # SENSORES → ML (Feedback loop)
    # ========================================
    event_bus.subscribe_async(LecturaRegistradaEvent, handlers.feed_ml_model_from_sensor_reading)
    logger.info("✅ Sensores → ML (1 handler)")
    
    # ========================================
    # FALLAS → ML (Feedback loop)
    # ========================================
    event_bus.subscribe_async(FallaResueltaEvent, handlers.update_ml_model_from_fault_resolution)
    logger.info("✅ Fallas → ML (1 handler)")
    
    # ========================================
    # MOTOS → MANTENIMIENTO (Verificaciones)
    # ========================================
    event_bus.subscribe_async(KilometrajeUpdatedEvent, handlers.check_maintenance_on_kilometraje_update)
    logger.info("✅ Motos → Mantenimiento (1 handler)")
    
    # ========================================
    # MANTENIMIENTO → NOTIFICACIONES
    # ========================================
    event_bus.subscribe_async(MantenimientoUrgenteEvent, handlers.send_notification_for_maintenance_urgent)
    logger.info("✅ Mantenimiento → Notificaciones (1 handler)")
    
    # ========================================
    # AUTH → SUSCRIPCIONES (Auto-creación)
    # ========================================
    from .suscripciones import event_handlers as suscripciones_handlers
    suscripciones_handlers.register_event_handlers()
    logger.info("✅ Auth → Suscripciones (1 handler)")
    
    # ========================================
    # AUTH → NOTIFICACIONES
    # ========================================
    event_bus.subscribe_async(UserRegisteredEvent, handlers.send_welcome_email)
    event_bus.subscribe_async(PasswordResetRequestedEvent, handlers.send_password_reset_email)
    logger.info("✅ Auth → Notificaciones (2 handlers)")
    
    # ========================================
    # SUSCRIPCIONES → NOTIFICACIONES
    # ========================================
    event_bus.subscribe_async(SuscripcionUpgradedEvent, handlers.send_subscription_upgrade_confirmation)
    event_bus.subscribe_async(SuscripcionExpiredEvent, handlers.send_subscription_expiration_reminder)
    logger.info("✅ Suscripciones → Notificaciones (2 handlers)")
    
    # ========================================
    # CHATBOT → NOTIFICACIONES
    # ========================================
    event_bus.subscribe_async(LimiteAlcanzadoEvent, handlers.send_limit_reached_notification)
    logger.info("✅ Chatbot → Notificaciones (1 handler)")
    
    # Resumen
    total_sync = sum(len(h) for h in event_bus._subscribers.values())
    total_async = sum(len(h) for h in event_bus._async_subscribers.values())
    total_event_types = len(set(list(event_bus._subscribers.keys()) + list(event_bus._async_subscribers.keys())))
    logger.info(f"🎯 Total: {total_event_types} tipos de eventos, {total_sync + total_async} handlers ({total_sync} sync + {total_async} async)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Inicializa recursos al inicio y los limpia al finalizar.
    """
    # ============================================
    # STARTUP
    # ============================================
    print("🚀 Iniciando RIM Backend...")
    
    # Inicializar base de datos
    print("📊 Inicializando base de datos...")
    await init_db()
    
    # Configurar event bus (suscribir handlers de eventos)
    print("📡 Configurando Event Bus...")
    await setup_event_handlers()
    print(f"✅ Event Bus configurado con {len(event_bus._subscribers)} tipos de eventos sincrónicos y {len(event_bus._async_subscribers)} tipos de eventos asíncronos")
    
    print("✅ RIM Backend iniciado correctamente")
    
    yield
    
    # ============================================
    # SHUTDOWN
    # ============================================
    print("🛑 Cerrando RIM Backend...")
    
    # Cerrar conexiones de base de datos
    await close_db()
    
    # Limpiar event bus
    event_bus.clear()
    
    print("✅ RIM Backend cerrado correctamente")


# ============================================
# CREAR APLICACIÓN FASTAPI
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)


# ============================================
# MIDDLEWARE
# ============================================
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ROUTERS
# ============================================
# Autenticación y Usuarios
app.include_router(auth_router, prefix=f"{settings.API_PREFIX}/auth", tags=["Autenticación"])
app.include_router(usuarios_router, prefix=f"{settings.API_PREFIX}/usuarios", tags=["Usuarios"])

# Motos y Suscripciones
app.include_router(motos_router, prefix=f"{settings.API_PREFIX}/motos", tags=["Motos"])
app.include_router(suscripciones_router, prefix=f"{settings.API_PREFIX}/suscripciones", tags=["Suscripciones"])

# IoT y Sensores
app.include_router(sensores_router, prefix=f"{settings.API_PREFIX}/sensores", tags=["Sensores IoT"])
# WebSocket para telemetría en tiempo real
app.include_router(websocket_router, tags=["WebSocket Telemetría"])

# Fallas y Mantenimiento
app.include_router(fallas_router, prefix=f"{settings.API_PREFIX}/fallas", tags=["Gestión de Fallas"])
app.include_router(mantenimiento_router, prefix=f"{settings.API_PREFIX}/mantenimiento", tags=["Mantenimiento"])

# Machine Learning
app.include_router(ml_router, prefix=f"{settings.API_PREFIX}/ml", tags=["Machine Learning"])

# Chatbot y Notificaciones
app.include_router(chatbot_router, prefix=f"{settings.API_PREFIX}/chatbot", tags=["Chatbot IA"])
app.include_router(notificaciones_router, prefix=f"{settings.API_PREFIX}/notificaciones", tags=["Notificaciones"])


# ============================================
# ENDPOINTS DE SALUD
# ============================================
@app.get("/")
async def root():
    """Endpoint raíz."""
    return {
        "message": "🏍️ RIM - Sistema Inteligente de Moto",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": f"{settings.API_PREFIX}/docs"
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check para monitoreo con verificaciones de servicios."""
    
    # Verificar servicios críticos
    db_healthy = await check_db_connection()
    
    # Determinar estado general
    status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": status,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "healthy" if db_healthy else "unhealthy",
            "api": "healthy"
        }
    }



@app.get(f"{settings.API_PREFIX}/status")
async def api_status() -> Dict[str, Any]:
    """Estado de la API y servicios."""
    # Verificar estado de servicios
    db_status = await check_db_connection()
    
    # Verificar Ollama
    ollama_status = False
    try:
        llm_provider = get_llm_provider()
        ollama_status = await llm_provider.health_check()
    except Exception as e:
        logger.warning(f"Error verificando Ollama: {e}")
    
    # TODO: Agregar verificación de Redis cuando se implemente
    redis_status = "not_implemented"
    
    return {
        "api": "running",
        "database": "connected" if db_status else "disconnected",
        "ollama": "connected" if ollama_status else "disconnected",
        "redis": redis_status,
        "features": {
            "freemium_enabled": True,
            "premium_enabled": True,
            "ml_enabled": True,
            "chatbot_enabled": ollama_status,  # Chatbot requiere Ollama
            "sensor_simulation": settings.SENSOR_SIMULATION_ENABLED
        },
        "event_bus": {
            "active": True,
            "event_types": len(event_bus._subscribers),
            "total_handlers": sum(len(handlers) for handlers in event_bus._subscribers.values())
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=(settings.LOG_LEVEL or "info").lower()
    )