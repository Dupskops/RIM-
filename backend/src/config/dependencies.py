"""
Dependencies globales de FastAPI.
Proporciona utilidades comunes para inyección de dependencias.
"""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from .settings import settings
from .database import get_db
from ..shared.exceptions import (
    UnauthorizedException,
    ForbiddenException,
)


# ============================================
# AUTENTICACIÓN JWT
# ============================================
async def get_token_from_header(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extrae el token JWT del header Authorization.
    
    Args:
        authorization: Header "Authorization: Bearer <token>"
        
    Returns:
        Token JWT o None si no existe
    """
    if not authorization:
        return None
    
    # Formato esperado: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


async def decode_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Payload del token
        
    Raises:
        UnauthorizedException: Si el token es inválido o expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise UnauthorizedException(f"Token inválido: {str(e)}")


async def get_current_user_id(
    token: Optional[str] = Depends(get_token_from_header)
) -> str:
    """
    Obtiene el ID del usuario autenticado desde el token JWT.
    
    Uso:
        @router.get("/protected")
        async def protected_route(
            user_id: str = Depends(get_current_user_id)
        ):
            return {"user_id": user_id}
    
    Raises:
        UnauthorizedException: Si no hay token o es inválido
    """
    if not token:
        raise UnauthorizedException("Token de autenticación requerido")
    
    payload = await decode_token(token)
    user_id = payload.get("sub")  # "sub" es el claim estándar para user_id
    
    if not user_id:
        raise UnauthorizedException("Token inválido: falta user_id")
    
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el objeto Usuario completo desde la base de datos.
    
    Uso:
        @router.get("/me")
        async def get_profile(
            user = Depends(get_current_user)
        ):
            return user
    
    Raises:
        UnauthorizedException: Si el usuario no existe
    """
    # Importación tardía para evitar dependencias circulares
    from ..usuarios.repositories import UsuarioRepository
    
    repo = UsuarioRepository(db)
    # Convertir user_id de string (JWT) a int (DB)
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException("ID de usuario inválido")
    
    user = await repo.get_by_id(user_id_int)
    
    if not user:
        raise UnauthorizedException("Usuario no encontrado")
    
    return user


async def get_optional_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el usuario si está autenticado, None si no.
    Útil para endpoints que funcionan con y sin autenticación.
    
    Uso:
        @router.get("/public-but-personalized")
        async def public_route(
            user = Depends(get_optional_user)
        ):
            if user:
                return {"message": f"Hola {user.nombre}"}
            return {"message": "Hola invitado"}
    """
    if not token:
        return None
    
    try:
        payload = await decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Convertir user_id de string (JWT) a int (DB)
        user_id_int = int(user_id)
        
        from ..usuarios.repositories import UsuarioRepository
        repo = UsuarioRepository(db)
        return await repo.get_by_id(user_id_int)
    except:
        return None


# ============================================
# AUTORIZACIÓN POR ROLES
# ============================================
def require_auth():
    """
    Dependency que requiere autenticación.
    Alias más explícito de get_current_user_id.
    
    Uso:
        @router.get("/protected")
        async def protected(
            _auth = Depends(require_auth())
        ):
            return {"message": "Autorizado"}
    """
    return get_current_user_id


def require_admin(
    user = Depends(get_current_user)
):
    """
    Dependency que requiere rol de administrador.
    
    Uso:
        @router.post("/admin/users")
        async def admin_only(
            _admin = Depends(require_admin)
        ):
            return {"message": "Admin autorizado"}
    
    Raises:
        ForbiddenException: Si el usuario no es admin
    """
    from ..shared.constants import UserRole
    
    if not user.rol or user.rol != "admin":
        raise ForbiddenException(
            "Se requieren permisos de administrador"
        )
    
    return user


def require_role(required_role: str):
    """
    Factory que crea un dependency para verificar un rol específico.
    
    Uso:
        from ..shared.constants import UserRole
        
        @router.get("/mecanico/tools")
        async def mecanico_route(
            _mecanico = Depends(require_role(UserRole.MECANICO))
        ):
            return {"tools": [...]}
    """
    async def check_role(user = Depends(get_current_user)):
        if not hasattr(user, 'rol') or user.rol != required_role:
            raise ForbiddenException(
                f"Se requiere rol: {required_role}"
            )
        return user
    
    return check_role


# ============================================
# VALIDACIÓN DE RECURSOS
# ============================================
async def verify_moto_ownership(
    moto_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """
    Verifica que la moto pertenezca al usuario autenticado.
    
    Uso:
        @router.get("/motos/{moto_id}")
        async def get_moto(
            moto_id: str,
            _ownership: bool = Depends(verify_moto_ownership)
        ):
            return {"moto": moto_id}
    
    Raises:
        ForbiddenException: Si la moto no pertenece al usuario
    """
    # Importación tardía
    from ..motos.repositories import MotoRepository
    
    repo = MotoRepository(db)
    moto = await repo.get_by_id(moto_id)
    
    if not moto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moto no encontrada"
        )
    
    if moto.usuario_id != user_id:
        raise ForbiddenException(
            "No tienes permisos para acceder a esta moto KTM"
        )
    
    return True


# ============================================
# PAGINACIÓN
# ============================================
class PaginationParams:
    """
    Parámetros de paginación estándar.
    
    Uso:
        @router.get("/items")
        async def list_items(
            pagination: PaginationParams = Depends()
        ):
            return await repo.get_paginated(
                page=pagination.page,
                page_size=pagination.page_size
            )
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
    
    @property
    def skip(self) -> int:
        """Calcula offset para la query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Retorna el límite para la query."""
        return self.page_size


# ============================================
# VALIDACIÓN DE MARCA KTM
# ============================================
async def verify_ktm_brand(
    moto_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica que la moto sea de marca KTM.
    Útil para features específicas de KTM.
    
    Raises:
        HTTPException: Si la moto no es KTM
    """
    from ..motos.repositories import MotoRepository
    
    repo = MotoRepository(db)
    moto = await repo.get_by_id(moto_id)
    
    if not moto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moto no encontrada"
        )
    
    if moto.marca.upper() != "KTM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta funcionalidad solo está disponible para motos KTM"
        )
    
    return True


# ============================================
# RATE LIMITING (Placeholder para futuro)
# ============================================
class RateLimitParams:
    """
    Parámetros para rate limiting.
    Placeholder para implementación futura.
    """
    
    def __init__(
        self,
        requests: int = 100,
        window: int = 60  # segundos
    ):
        self.requests = requests
        self.window = window