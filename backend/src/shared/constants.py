"""
Constantes globales del sistema RIM.
"""
from enum import Enum


# ============================================
# PLANES DE SUSCRIPCIÓN
# ============================================
class PlanType(str, Enum):
    """Tipos de planes de suscripción."""
    FREEMIUM = "freemium"
    PREMIUM = "premium"
    TRIAL = "trial"


class EstadoSuscripcion(str, Enum):
    """Estados de una suscripción."""
    ACTIVA = "activa"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"
    PENDIENTE = "pendiente"
    TRIAL = "trial"


class TipoSuscripcion(str, Enum):
    """Tipos de suscripción (alias de PlanType para consistencia)."""
    FREEMIUM = "freemium"
    PREMIUM = "premium"
    TRIAL = "trial"


# ============================================
# FEATURES POR PLAN
# ============================================
class Feature(str, Enum):
    """Features disponibles en el sistema."""
    # Freemium
    ALERTAS_BASICAS = "alertas_basicas"
    HISTORIAL_SERVICIOS = "historial_servicios"
    DIAGNOSTICO_GENERAL = "diagnostico_general"
    GEOLOCALIZACION_BASICA = "geolocalizacion_basica"
    CHATBOT_BASICO = "chatbot_basico"
    
    # Premium
    MODOS_MANEJO = "modos_manejo"
    DIAGNOSTICO_PREDICTIVO_AVANZADO_IA = "diagnostico_predictivo_ia"
    ACTUALIZACIONES_OTA = "actualizaciones_ota"
    ASISTENCIA_REMOTA_24_7 = "asistencia_remota_24_7"
    INTEGRACION_WEARABLES = "integracion_wearables"
    REPORTES_AVANZADOS = "reportes_avanzados"
    CHATBOT_AVANZADO = "chatbot_avanzado"


# Mapeo de features a planes
FREEMIUM_FEATURES = [
    Feature.ALERTAS_BASICAS,
    Feature.HISTORIAL_SERVICIOS,
    Feature.DIAGNOSTICO_GENERAL,
    Feature.GEOLOCALIZACION_BASICA,
    Feature.CHATBOT_BASICO,
]

PREMIUM_FEATURES = FREEMIUM_FEATURES + [
    Feature.MODOS_MANEJO,
    Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA,
    Feature.ACTUALIZACIONES_OTA,
    Feature.ASISTENCIA_REMOTA_24_7,
    Feature.INTEGRACION_WEARABLES,
    Feature.REPORTES_AVANZADOS,
    Feature.CHATBOT_AVANZADO,
]


# ============================================
# SENSORES
# ============================================
class TipoSensor(str, Enum):
    """Tipos de sensores en la moto."""
    TEMPERATURA_MOTOR = "temperatura_motor"
    TEMPERATURA_ACEITE = "temperatura_aceite"
    PRESION_ACEITE = "presion_aceite"
    VOLTAJE_BATERIA = "voltaje_bateria"
    PRESION_LLANTA_DELANTERA = "presion_llanta_delantera"
    PRESION_LLANTA_TRASERA = "presion_llanta_trasera"
    VIBRACIONES = "vibraciones"
    RPM = "rpm"
    VELOCIDAD = "velocidad"
    GPS_LATITUD = "gps_latitud"
    GPS_LONGITUD = "gps_longitud"
    ACELEROMETRO_X = "acelerometro_x"
    ACELEROMETRO_Y = "acelerometro_y"
    ACELEROMETRO_Z = "acelerometro_z"
    NIVEL_COMBUSTIBLE = "nivel_combustible"


# Rangos normales de sensores (para detección de anomalías)
SENSOR_RANGES = {
    TipoSensor.TEMPERATURA_MOTOR: {"min": 60, "max": 90, "unit": "°C"},
    TipoSensor.TEMPERATURA_ACEITE: {"min": 70, "max": 110, "unit": "°C"},
    TipoSensor.PRESION_ACEITE: {"min": 2.0, "max": 5.0, "unit": "bar"},
    TipoSensor.VOLTAJE_BATERIA: {"min": 12.5, "max": 14.5, "unit": "V"},
    TipoSensor.PRESION_LLANTA_DELANTERA: {"min": 30, "max": 36, "unit": "PSI"},
    TipoSensor.PRESION_LLANTA_TRASERA: {"min": 32, "max": 38, "unit": "PSI"},
    TipoSensor.VIBRACIONES: {"min": 0, "max": 3.0, "unit": "g"},
    TipoSensor.RPM: {"min": 800, "max": 12000, "unit": "RPM"},
    TipoSensor.VELOCIDAD: {"min": 0, "max": 200, "unit": "km/h"},
    TipoSensor.NIVEL_COMBUSTIBLE: {"min": 0, "max": 100, "unit": "%"},
}


# ============================================
# FALLAS
# ============================================
class TipoFalla(str, Enum):
    """Tipos de fallas detectables."""
    SOBRECALENTAMIENTO = "sobrecalentamiento"
    BATERIA_BAJA = "bateria_baja"
    PRESION_ACEITE_BAJA = "presion_aceite_baja"
    VIBRACIONES_ANORMALES = "vibraciones_anormales"
    PRESION_LLANTAS_INCORRECTA = "presion_llantas_incorrecta"
    SENSOR_DESCONECTADO = "sensor_desconectado"
    CAIDA_DETECTADA = "caida_detectada"
    NIVEL_COMBUSTIBLE_CRITICO = "nivel_combustible_critico"


class SeveridadFalla(str, Enum):
    """Niveles de severidad de fallas."""
    INFO = "info"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoFalla(str, Enum):
    """Estados de una falla."""
    DETECTADA = "detectada"
    EN_REVISION = "en_revision"
    RESUELTA = "resuelta"
    IGNORADA = "ignorada"


# ============================================
# NOTIFICACIONES
# ============================================
class TipoNotificacion(str, Enum):
    """Tipos de notificaciones."""
    ALERTA_SENSOR = "alerta_sensor"
    FALLA_DETECTADA = "falla_detectada"
    MANTENIMIENTO_PROGRAMADO = "mantenimiento_programado"
    MANTENIMIENTO_VENCIDO = "mantenimiento_vencido"
    PREDICCION_FALLA = "prediccion_falla"
    ACTUALIZACION_DISPONIBLE = "actualizacion_disponible"
    SUSCRIPCION_ACTUALIZADA = "suscripcion_actualizada"
    TRIAL_EXPIRANDO = "trial_expirando"


class CanalNotificacion(str, Enum):
    """Canales de envío de notificaciones."""
    WEBSOCKET = "websocket"
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


# ============================================
# MANTENIMIENTO
# ============================================
class TipoMantenimiento(str, Enum):
    """Tipos de mantenimiento."""
    CAMBIO_ACEITE = "cambio_aceite"
    CAMBIO_FILTRO_AIRE = "cambio_filtro_aire"
    CAMBIO_LLANTAS = "cambio_llantas"
    REVISION_FRENOS = "revision_frenos"
    AJUSTE_CADENA = "ajuste_cadena"
    REVISION_GENERAL = "revision_general"
    CAMBIO_BATERIA = "cambio_bateria"
    CAMBIO_BUJIAS = "cambio_bujias"


class EstadoMantenimiento(str, Enum):
    """Estados de mantenimiento."""
    PENDIENTE = "pendiente"
    PROGRAMADO = "programado"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"


# ============================================
# ROLES DE USUARIO
# ============================================
class UserRole(str, Enum):
    """Roles de usuarios."""
    USUARIO = "usuario"
    ADMIN = "admin"
    MECANICO = "mecanico"
    SOPORTE = "soporte"


# ============================================
# WEBSOCKET
# ============================================
class WSMessageType(str, Enum):
    """Tipos de mensajes WebSocket."""
    # Cliente → Servidor
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    CHAT_MESSAGE = "chat_message"
    
    # Servidor → Cliente
    PONG = "pong"
    NOTIFICATION = "notification"
    SENSOR_UPDATE = "sensor_update"
    CHAT_RESPONSE = "chat_response"
    ERROR = "error"


# ============================================
# MODOS DE CONDUCCIÓN (Premium)
# ============================================
class ModoConductor(str, Enum):
    """Modos de conducción disponibles."""
    ECO = "eco"
    SPORT = "sport"
    URBANO = "urbano"
    OFF_ROAD = "off_road"
    CUSTOM = "custom"


# ============================================
# CONFIGURACIÓN DE CACHE
# ============================================
CACHE_TTL = {
    "user_permissions": 3600,  # 1 hora
    "sensor_readings": 60,  # 1 minuto
    "moto_info": 1800,  # 30 minutos
    "subscription_status": 300,  # 5 minutos
}


# ============================================
# LÍMITES Y UMBRALES
# ============================================
MAX_SENSOR_READINGS_PER_BATCH = 100
MAX_NOTIFICATIONS_PER_USER = 50
MAX_CHAT_HISTORY_MESSAGES = 20
ML_PREDICTION_THRESHOLD = 0.75
SENSOR_ANOMALY_THRESHOLD = 0.8
