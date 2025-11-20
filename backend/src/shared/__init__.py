"""
Módulo shared - Código compartido del sistema RIM.
Proporciona utilidades, constantes, excepciones y más.
"""

# Event Bus
from .event_bus import Event, EventBus, event_bus

# Modelos Base de API
from .base_models import (
    ApiResponse,
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
    PaginatedResponse,
    ListResponse,
    PaginationMeta,
    PaginationParams,
    SortParams,
    FilterParams,
    create_success_response,
    create_error_response,
    create_paginated_response,
)

# Excepciones
from .exceptions import (
    RIMException,
    AuthenticationException,
    UnauthorizedException,
    ForbiddenException,
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    ValidationException,
    PremiumRequiredException,
    PremiumFeatureException,
    SubscriptionException,
    BusinessLogicException,
    MotoNotFoundException,
    SensorException,
    MLException,
    ChatbotException,
    ExternalServiceException,
    OllamaException,
)

# Constantes
from .constants import (
    PlanType,
    EstadoSuscripcion,
    TipoSuscripcion,
    Feature,
    FREEMIUM_FEATURES,
    PREMIUM_FEATURES,
    TipoSensor,
    SENSOR_RANGES,
    TipoNotificacion,
    CanalNotificacion,
    TipoMantenimiento,
    EstadoMantenimiento,
    UserRole,
    WSMessageType,
    ModoConductor,
    CACHE_TTL,
)

# Utilidades
from .utils import (
    now,
    add_days,
    is_expired,
    format_datetime,
    days_until,
    generate_token,
    hash_string,
    is_valid_email,
    is_valid_phone,
    sanitize_string,
    safe_divide,
    clamp,
    percentage,
    round_to_decimals,
    format_sensor_value,
    truncate_text,
    paginate,
    generate_id,
    is_valid_uuid,
)

# Middleware
from .middleware import (
    check_feature_access,
    require_premium,
    require_features,
    FeatureChecker,
    get_required_plan_for_feature,
    get_upgrade_url,
)

# WebSocket
from .websocket import (
    ConnectionManager,
    connection_manager,
    BaseWebSocketHandler,
    get_token_from_websocket,
    authenticate_websocket,
    verify_websocket_permissions,
    WebSocketAuthMiddleware,
    require_premium as ws_require_premium,
    require_moto_ownership,
    require_admin,
    log_websocket_event,
    rate_limit,
    validate_message_schema,
    auto_rejoin_room,
    check_premium_subscription,
    check_moto_ownership,
    check_admin_role,
    check_notification_permission,
    check_chatbot_access,
    check_sensor_access,
    check_maintenance_access,
    check_failure_access,
    verify_websocket_permission,
    WebSocketPermissionChecker,
)

__all__ = [
    # Event Bus
    "Event",
    "EventBus",
    "event_bus",
    
    # Modelos Base de API
    "ApiResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "ListResponse",
    "PaginationMeta",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "create_success_response",
    "create_error_response",
    "create_paginated_response",
    
    # Excepciones
    "RIMException",
    "AuthenticationException",
    "UnauthorizedException",
    "ForbiddenException",
    "ResourceNotFoundException",
    "ResourceAlreadyExistsException",
    "ValidationException",
    "PremiumRequiredException",
    "PremiumFeatureException",
    "SubscriptionException",
    "BusinessLogicException",
    "MotoNotFoundException",
    "SensorException",
    "MLException",
    "ChatbotException",
    "ExternalServiceException",
    "OllamaException",
    
    # Constantes
    "PlanType",
    "EstadoSuscripcion",
    "TipoSuscripcion",
    "Feature",
    "FREEMIUM_FEATURES",
    "PREMIUM_FEATURES",
    "TipoSensor",
    "SENSOR_RANGES",
    "TipoNotificacion",
    "CanalNotificacion",
    "TipoMantenimiento",
    "EstadoMantenimiento",
    "UserRole",
    "WSMessageType",
    "ModoConductor",
    "CACHE_TTL",
    
    # Utilidades
    "now",
    "add_days",
    "is_expired",
    "format_datetime",
    "days_until",
    "generate_token",
    "hash_string",
    "is_valid_email",
    "is_valid_phone",
    "sanitize_string",
    "safe_divide",
    "clamp",
    "percentage",
    "round_to_decimals",
    "format_sensor_value",
    "truncate_text",
    "paginate",
    "generate_id",
    "is_valid_uuid",
    
    # Middleware
    "check_feature_access",
    "require_premium",
    "require_features",
    "FeatureChecker",
    "get_required_plan_for_feature",
    "get_upgrade_url",
    
    # WebSocket - Connection Manager
    "ConnectionManager",
    "connection_manager",
    
    # WebSocket - Handler Base
    "BaseWebSocketHandler",
    
    # WebSocket - Autenticación
    "get_token_from_websocket",
    "authenticate_websocket",
    "verify_websocket_permissions",
    "WebSocketAuthMiddleware",
    
    # WebSocket - Decoradores
    "ws_require_premium",  # Aliased to avoid conflict with middleware.require_premium
    "require_moto_ownership",
    "require_admin",
    "log_websocket_event",
    "rate_limit",
    "validate_message_schema",
    "auto_rejoin_room",
    
    # WebSocket - Permisos
    "check_premium_subscription",
    "check_moto_ownership",
    "check_admin_role",
    "check_notification_permission",
    "check_chatbot_access",
    "check_sensor_access",
    "check_maintenance_access",
    "check_failure_access",
    "verify_websocket_permission",
    "WebSocketPermissionChecker",
]
