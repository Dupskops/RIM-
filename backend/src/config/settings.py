"""
Configuración centralizada del proyecto RIM.
Usa pydantic-settings para validar variables de entorno.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Configuración principal de la aplicación."""
    
    # ============================================
    # APLICACIÓN
    # ============================================
    APP_NAME: str = "RIM - Sistema Inteligente de Moto"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API Backend para gestión de motos inteligentes con IA"
    DEBUG: bool = False
    API_PREFIX: str = "/api"
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "DEBUG"
    LOG_COLORS: bool = True
    COLORAMA_ENABLED: bool = True
    # Usar loguru como backend de logging (si True, loguru interceptará logging estándar)
    LOG_USE_LOGURU: bool = False
    # Formato opcional para Loguru (si se desea personalizar)
    # Formato por defecto para Loguru: incluye una tabulación entre el nombre y el mensaje
    LOGURU_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}\t{message}"
    # Lista de loggers a forzar en DEBUG (vacío por defecto).
    # Preferible controlar el nivel de logging global mediante LOG_LEVEL.
    LOG_MODULE_DEBUG: list[str] = []
    # Mapear módulos (clave: nombre corto del módulo dentro de src, p.ej. 'auth')
    # a códigos ANSI para colorear específicamente cada módulo. Si está vacío,
    # se usa la paleta determinística por hash.
    LOG_MODULE_COLORS: dict[str, str] = {
        "auth": "\x1b[94m",         # bright blue
        "usuarios": "\x1b[95m",     # bright magenta
        "motos": "\x1b[92m",        # bright green
        "suscripciones": "\x1b[96m",# bright cyan
        "sensores": "\x1b[93m",     # bright yellow
        "fallas": "\x1b[91m",       # bright red
        "mantenimiento": "\x1b[90m",# bright black / grey
        "chatbot": "\x1b[94m",      # bright blue
        "notificaciones": "\x1b[96m",# bright cyan
        "ml": "\x1b[95m",           # bright magenta
        "integraciones": "\x1b[93m",# bright yellow
        "shared": "\x1b[92m",       # bright green
        "main": "\x1b[97m",         # bright white (único para entrypoint)
    }
    
    # ============================================
    # BASE DE DATOS
    # ============================================
    DATABASE_URL: str = "postgresql+asyncpg://rim_user:rim_password@localhost:5432/rim_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False  # Log de queries SQL
    
    # ============================================
    # REDIS (Cache & WebSocket PubSub)
    # ============================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hora
    
    # ============================================
    # AUTENTICACIÓN JWT
    # ============================================
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============================================
    # OLLAMA (LLM Local para Chatbot en Docker)
    # ============================================
    OLLAMA_BASE_URL: str = "http://ollama:11434"  # Nombre del servicio en docker-compose
    OLLAMA_MODEL: str = "llama2"  # Modelos: llama2, llama3, mistral, phi, codellama, etc.
    OLLAMA_TIMEOUT: int = 180
    OLLAMA_STREAM: bool = True
    
    # ============================================
    # MACHINE LEARNING
    # ============================================
    ML_MODEL_PATH: str = "./src/ml/trained_models"
    ML_INFERENCE_THRESHOLD: float = 0.75
    ML_BATCH_SIZE: int = 32
    
    # ============================================
    # WEBSOCKET
    # ============================================
    WS_HEARTBEAT_INTERVAL: int = 30  # segundos
    WS_MAX_CONNECTIONS: int = 1000
    
    # ============================================
    # SENSORES & SIMULACIÓN (MVP)
    # ============================================
    SENSOR_SIMULATION_ENABLED: bool = True  # Activar simulador para MVP
    SENSOR_READ_INTERVAL: int = 5  # segundos entre lecturas
    
    # ============================================
    # SUSCRIPCIONES (Freemium/Premium)
    # ============================================
    FREEMIUM_PLAN_ID: int = 1
    PREMIUM_PLAN_ID: int = 2
    TRIAL_DURATION_DAYS: int = 7
    PREMIUM_PRICE_MONTHLY: float = 9.99
    PREMIUM_PRICE_YEARLY: float = 99.99
    
    # ============================================
    # NOTIFICACIONES
    # ============================================
    NOTIFICATION_BATCH_SIZE: int = 100
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    
    # ============================================
    # CORS
    # ============================================
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # React dev
        "http://localhost:5173",  # Vite dev
        "http://localhost:4173",  # Vite build
        "http://localhost:8080",  # Producción local
    ]
    
    # ============================================
    # ADMIN PANEL (Para demos)
    # ============================================
    ADMIN_SECRET_KEY: str = "ADMIN_DEMO_KEY_CHANGE_IN_PRODUCTION"
    
    # ============================================
    # CONFIGURACIÓN ESPECÍFICA KTM
    # ============================================
    # Marca soportada (solo KTM en este proyecto)
    SUPPORTED_BRAND: str = "KTM"
    
    # Modelos KTM soportados (principales líneas)
    KTM_SUPPORTED_MODELS: list[str] = [
        "Duke",
        "RC",
        "Adventure",
        "Enduro",
        "SMC",
        "SuperDuke",
        "890",
        "790",
        "690",
        "490",
        "390",
        "250",
        "125",
    ]
    
    # Configuración de sensores específicos para motos KTM
    KTM_SENSOR_CONFIG: dict[str, float] = {
        "temperatura_motor_max": 95.0,  # °C
        "rpm_max": 11500,  # RPM para mayoría de KTM
        "presion_aceite_min": 2.5,  # bar
        "voltaje_bateria_min": 12.3,  # V
    }
    
    # Features específicas de KTM
    KTM_FEATURES_ENABLED: bool = True
    KTM_RIDE_MODES: list[str] = ["Street", "Sport", "Rain", "Off-road"]
    
    # Integración con servicios KTM (futuro)
    KTM_API_URL: Optional[str] = None  # API oficial de KTM si estuviera disponible
    KTM_DEALER_NETWORK_ENABLED: bool = False  # Red de concesionarios
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
        # No intentar parsear JSON automáticamente para listas
        env_parse_none_str="null",
    )


# Instancia global de configuración
settings = Settings()