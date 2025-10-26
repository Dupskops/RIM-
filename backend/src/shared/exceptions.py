"""
Excepciones personalizadas del sistema RIM.
Proporciona manejo consistente de errores.
"""
from fastapi import HTTPException, status


class RIMException(Exception):
    """Excepción base para todas las excepciones del sistema."""
    
    def __init__(self, message: str, code: str = "RIM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ============================================
# EXCEPCIONES DE AUTENTICACIÓN
# ============================================
class AuthenticationException(RIMException):
    """Excepción para errores de autenticación."""
    
    def __init__(self, message: str = "Error de autenticación"):
        super().__init__(message, "AUTH_ERROR")


class UnauthorizedException(HTTPException):
    """Usuario no autenticado."""
    
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    """Usuario autenticado pero sin permisos."""
    
    def __init__(self, detail: str = "No tiene permisos para esta acción"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# ============================================
# EXCEPCIONES DE RECURSOS
# ============================================
class ResourceNotFoundException(HTTPException):
    """Recurso no encontrado."""
    
    def __init__(self, resource: str, resource_id: int | str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} con ID {resource_id} no encontrado",
        )


class ResourceAlreadyExistsException(HTTPException):
    """Recurso ya existe."""
    
    def __init__(self, resource: str, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource}: {detail}",
        )


# ============================================
# EXCEPCIONES DE VALIDACIÓN
# ============================================
class ValidationException(HTTPException):
    """Error de validación de datos."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


# ============================================
# EXCEPCIONES DE SUSCRIPCIONES
# ============================================
class PremiumRequiredException(HTTPException):
    """Acción requiere suscripción Premium."""
    
    def __init__(
        self, 
        feature: str,
        detail: str | None = None
    ):
        message = detail or f"Esta función requiere plan Premium: {feature}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message,
            headers={"X-Premium-Required": "true"},
        )


class SubscriptionException(RIMException):
    """Excepción para errores relacionados con suscripciones."""
    
    def __init__(self, message: str):
        super().__init__(message, "SUBSCRIPTION_ERROR")


# Alias para compatibilidad
PremiumFeatureException = PremiumRequiredException


# ============================================
# EXCEPCIONES DE NEGOCIO
# ============================================
class BusinessLogicException(HTTPException):
    """Error de lógica de negocio."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class MotoNotFoundException(ResourceNotFoundException):
    """Moto no encontrada."""
    
    def __init__(self, moto_id: str):
        super().__init__("Moto", moto_id)


class SensorException(RIMException):
    """Excepción para errores de sensores."""
    
    def __init__(self, message: str):
        super().__init__(message, "SENSOR_ERROR")


class MLException(RIMException):
    """Excepción para errores de Machine Learning."""
    
    def __init__(self, message: str):
        super().__init__(message, "ML_ERROR")


class ChatbotException(RIMException):
    """Excepción para errores del chatbot."""
    
    def __init__(self, message: str):
        super().__init__(message, "CHATBOT_ERROR")


# ============================================
# EXCEPCIONES EXTERNAS
# ============================================
class ExternalServiceException(HTTPException):
    """Error al comunicarse con servicio externo."""
    
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en servicio {service}: {detail}",
        )


class OllamaException(ExternalServiceException):
    """Error al comunicarse con Ollama."""
    
    def __init__(self, detail: str):
        super().__init__("Ollama", detail)
