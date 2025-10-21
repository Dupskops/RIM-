"""
Middleware y decoradores para control de acceso basado en suscripciones.
Implementa el sistema Freemium/Premium.
"""
from functools import wraps
from typing import Callable, TYPE_CHECKING
from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import Feature, PlanType, FREEMIUM_FEATURES, PREMIUM_FEATURES
from .exceptions import PremiumRequiredException, UnauthorizedException

# Importación condicional para evitar circular imports
if TYPE_CHECKING:
    from ..config.database import get_db


# ============================================
# VERIFICACIÓN DE PERMISOS
# ============================================
async def check_feature_access(
    user_id: str,
    feature: Feature,
    db: AsyncSession
) -> bool:
    """
    Verifica si un usuario tiene acceso a una feature específica.
    
    Args:
        user_id: ID del usuario
        feature: Feature a verificar
        db: Sesión de base de datos
        
    Returns:
        True si tiene acceso, False si no
    """
    # Importación tardía para evitar dependencias circulares
    from ..suscripciones.services import SubscriptionService
    
    service = SubscriptionService(db)
    
    try:
        subscription = await service.get_active_subscription(user_id)
        
        # Verificar según el plan
        if subscription.plan.nombre == PlanType.PREMIUM or subscription.estado == "trial":
            return feature in PREMIUM_FEATURES
        elif subscription.plan.nombre == PlanType.FREEMIUM:
            return feature in FREEMIUM_FEATURES
        else:
            return False
            
    except Exception:
        # Si no hay suscripción, solo acceso freemium
        return feature in FREEMIUM_FEATURES


def require_premium(feature: Feature):
    """
    Decorador para endpoints que requieren Premium.
    
    Uso:
        @router.get("/diagnostico-predictivo")
        @require_premium(Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA)
        async def diagnostico_predictivo(
            usuario_id: str = Depends(get_current_user_id),
            db: AsyncSession = Depends(get_db)
        ):
            return {"prediccion": "..."}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer dependencias del request
            request: Request = kwargs.get("request")
            db: AsyncSession = kwargs.get("db")
            
            # Obtener user_id del token JWT (implementar en auth)
            user_id = getattr(request.state, "user_id", None)
            
            if not user_id:
                raise UnauthorizedException("Usuario no autenticado")
            
            # Verificar acceso a la feature
            has_access = await check_feature_access(user_id, feature, db)
            
            if not has_access:
                raise PremiumRequiredException(
                    feature=feature.value,
                    detail=f"Necesitas plan Premium para acceder a: {feature.value}"
                )
            
            # Si tiene acceso, ejecutar función original
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_features(*features: Feature):
    """
    Decorador para endpoints que requieren múltiples features.
    
    Uso:
        @router.get("/reportes-completos")
        @require_features(
            Feature.REPORTES_AVANZADOS,
            Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA
        )
        async def reportes_completos(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            db: AsyncSession = kwargs.get("db")
            user_id = getattr(request.state, "user_id", None)
            
            if not user_id:
                raise UnauthorizedException("Usuario no autenticado")
            
            # Verificar todas las features
            for feature in features:
                has_access = await check_feature_access(user_id, feature, db)
                if not has_access:
                    raise PremiumRequiredException(
                        feature=feature.value,
                        detail=f"Necesitas todas estas features: {', '.join(f.value for f in features)}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================
# DEPENDENCY PARA FASTAPI
# ============================================
class FeatureChecker:
    """
    Dependency para verificar acceso a features en endpoints.
    
    Uso:
        @router.get("/diagnostico")
        async def diagnostico(
            feature_check = Depends(
                FeatureChecker(Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA)
            )
        ):
            # Si llega aquí, tiene acceso
            return {"status": "ok"}
    """
    
    def __init__(self, feature: Feature):
        self.feature = feature
    
    async def __call__(
        self,
        request: Request,
    ):
        # Importación lazy para evitar circular import
        from ..config.database import get_db, AsyncSessionLocal
        
        # Obtener db session manualmente para evitar problemas con Depends
        async with AsyncSessionLocal() as db:
            user_id = getattr(request.state, "user_id", None)
            
            if not user_id:
                raise UnauthorizedException("Usuario no autenticado")
            
            has_access = await check_feature_access(user_id, self.feature, db)
            
            if not has_access:
                raise PremiumRequiredException(
                    feature=self.feature.value,
                    detail=f"Esta función requiere plan Premium"
                )
            
            return True


# ============================================
# MIDDLEWARE DE PERMISOS
# ============================================
class PermissionMiddleware:
    """
    Middleware global que verifica permisos antes de cada request.
    (Opcional - puede ser invasivo)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Aquí puedes implementar verificación global
        # Por ahora solo pasa el request
        await self.app(scope, receive, send)


# ============================================
# UTILIDADES
# ============================================
def get_required_plan_for_feature(feature: Feature) -> PlanType:
    """Retorna el plan mínimo requerido para una feature."""
    if feature in FREEMIUM_FEATURES:
        return PlanType.FREEMIUM
    elif feature in PREMIUM_FEATURES:
        return PlanType.PREMIUM
    else:
        return PlanType.PREMIUM  # Por defecto, features desconocidas requieren Premium


def get_upgrade_url(feature: Feature) -> str:
    """Retorna la URL para upgrade a Premium."""
    return f"/planes/premium?feature={feature.value}"
