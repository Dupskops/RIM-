"""
Validadores de reglas de negocio para el chatbot.
"""
from typing import Optional, Any


def validate_message_length(message: str, max_length: int = 10000) -> bool:
    """Valida que el mensaje no exceda la longitud máxima."""
    return len(message) <= max_length


def validate_conversation_id(conversation_id: str) -> bool:
    """Valida formato del conversation_id."""
    return len(conversation_id) > 0 and len(conversation_id) <= 100


def validate_tipo_prompt(tipo: Optional[str]) -> bool:
    """Valida que el tipo de prompt sea válido."""
    if tipo is None:
        return True
    
    tipos_validos = ["diagnostic", "maintenance", "explanation", "general"]
    return tipo in tipos_validos


def can_send_message_freemium(mensajes_hoy: int, max_mensajes: int = 50) -> bool:
    """Verifica si un usuario freemium puede enviar más mensajes hoy."""
    return mensajes_hoy < max_mensajes


def can_send_message_premium(mensajes_hoy: int, max_mensajes: int = 1000) -> bool:
    """Verifica si un usuario premium puede enviar más mensajes hoy."""
    return mensajes_hoy < max_mensajes


def can_use_advanced_features(nivel_acceso: str) -> bool:
    """Verifica si el usuario puede usar features avanzadas."""
    return nivel_acceso == "premium"


def validate_feedback(util: bool, feedback: Optional[str]) -> bool:
    """Valida que el feedback sea válido."""
    if feedback and len(feedback) > 1000:
        return False
    return True


def should_limit_context(nivel_acceso: str) -> bool:
    """Determina si se debe limitar el contexto de la conversación."""
    return nivel_acceso == "freemium"


def get_max_context_messages(nivel_acceso: str) -> int:
    """Obtiene el número máximo de mensajes de contexto según el nivel."""
    if nivel_acceso == "premium":
        return 20  # Últimos 20 mensajes
    return 5  # Freemium: últimos 5 mensajes


def get_max_tokens(nivel_acceso: str) -> int:
    """Obtiene el máximo de tokens permitidos por respuesta."""
    if nivel_acceso == "premium":
        return 2000
    return 500


def validate_streaming_support(nivel_acceso: str) -> bool:
    """Valida si el nivel de acceso soporta streaming."""
    # Ambos niveles soportan streaming
    return True


def calculate_confidence_threshold(nivel_acceso: str) -> float:
    """Calcula el umbral de confianza mínimo para respuestas."""
    if nivel_acceso == "premium":
        return 0.6  # 60% confianza mínima
    return 0.7  # 70% para freemium (más restrictivo)


def should_use_advanced_model(nivel_acceso: str, tipo_prompt: str) -> bool:
    """Determina si debe usar modelo avanzado."""
    if nivel_acceso != "premium":
        return False
    
    # Usar modelo avanzado para diagnósticos y mantenimiento en premium
    return tipo_prompt in ["diagnostic", "maintenance"]


def validate_conversation_title(titulo: str) -> bool:
    """Valida que el título de conversación sea válido."""
    return 1 <= len(titulo) <= 200


def can_delete_conversation(usuario_id: int, conversacion_usuario_id: int) -> bool:
    """Verifica si el usuario puede eliminar la conversación."""
    return usuario_id == conversacion_usuario_id


def can_clear_history(usuario_id: int, conversacion_usuario_id: int) -> bool:
    """Verifica si el usuario puede limpiar el historial."""
    return usuario_id == conversacion_usuario_id


def should_archive_conversation(dias_inactiva: int) -> bool:
    """Determina si una conversación debe archivarse."""
    return dias_inactiva > 30  # Archivar después de 30 días de inactividad


def validate_moto_access(usuario_id: int, moto_usuario_id: int) -> bool:
    """Verifica que el usuario tenga acceso a la moto."""
    return usuario_id == moto_usuario_id


def get_rate_limit_config(nivel_acceso: str) -> dict[str, int]:
    """Obtiene configuración de rate limiting según nivel."""
    if nivel_acceso == "premium":
        return {
            "max_messages": 100,  # 100 mensajes por minuto
            "window_seconds": 60,
            "max_tokens_per_day": 100000
        }
    else:  # freemium
        return {
            "max_messages": 20,  # 20 mensajes por minuto
            "window_seconds": 60,
            "max_tokens_per_day": 10000
        }


def validate_context_data(context: dict[str, Any]) -> bool:
    """Valida que los datos de contexto sean válidos."""
    # Verificar tamaño razonable (evitar contextos excesivos)
    import json
    try:
        context_str = json.dumps(context)
        return len(context_str) <= 50000  # Max 50KB de contexto
    except:
        return False


def should_use_diagnostic_prompt(message: str) -> bool:
    """Determina si debe usar prompt de diagnóstico basado en el mensaje."""
    keywords = [
        "problema", "falla", "error", "no funciona", "ruido", "extraño",
        "vibracion", "humo", "olor", "temperatura", "caliente", "frío",
        "bateria", "motor", "freno", "diagnostico", "que pasa", "que tiene"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in keywords)


def should_use_maintenance_prompt(message: str) -> bool:
    """Determina si debe usar prompt de mantenimiento."""
    keywords = [
        "mantenimiento", "servicio", "cambio", "aceite", "filtro", "llanta",
        "revision", "cuando", "cada cuanto", "cuanto cuesta", "precio",
        "taller", "reparacion", "repuesto"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in keywords)


def should_use_explanation_prompt(message: str) -> bool:
    """Determina si debe usar prompt de explicación."""
    keywords = [
        "que es", "como funciona", "para que sirve", "explica", "explicame",
        "como se", "por que", "porque", "cual es", "que significa", "ayuda"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in keywords)


def detect_prompt_type(message: str) -> str:
    """Detecta automáticamente el tipo de prompt basado en el mensaje."""
    if should_use_diagnostic_prompt(message):
        return "diagnostic"
    elif should_use_maintenance_prompt(message):
        return "maintenance"
    elif should_use_explanation_prompt(message):
        return "explanation"
    else:
        return "general"
