"""
Rutas de autenticación.
Define los endpoints HTTP para auth.
"""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.config.database import get_db
from src.config.dependencies import get_current_user_id
from .schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    UpdateProfileRequest,
    LoginResponse,
    UserResponse,
    TokenResponse,
    MessageResponse,
    TokenValidationResponse,
)
from .use_cases import (
    RegisterUserUseCase,
    LoginUserUseCase,
    RefreshTokenUseCase,
    LogoutUserUseCase,
    ChangePasswordUseCase,
    RequestPasswordResetUseCase,
    ResetPasswordUseCase,
    VerifyEmailUseCase,
)
from .repositories import UsuarioRepository
from src.shared.base_models import ApiResponse, SuccessResponse, create_success_response
#from src.shared import helpers

router = APIRouter()


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario con email y contraseña"
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registra un nuevo usuario y devuelve tokens de autenticación."""
    use_case = RegisterUserUseCase()
    result = await use_case.execute(db, data)
    
    return LoginResponse(
        user=UserResponse.from_orm(result["user"]),
        tokens=TokenResponse(**result["tokens"])
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión",
    description="Autentica un usuario con email y contraseña"
)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Autentica un usuario y devuelve tokens."""
    use_case = LoginUserUseCase()
    
    # Obtener IP y user agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    result = await use_case.execute(db, data, ip_address, user_agent)
    
    return LoginResponse(
        user=UserResponse.from_orm(result["user"]),
        tokens=TokenResponse(**result["tokens"])
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
    description="Obtiene un nuevo access token usando un refresh token válido"
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Renueva el access token."""
    use_case = RefreshTokenUseCase()
    result = await use_case.execute(db, data.refresh_token)
    
    return TokenResponse(**result)


@router.post(
    "/logout",
    response_model=SuccessResponse[None],
    summary="Cerrar sesión",
    description="Revoca el refresh token actual"
)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Cierra sesión del usuario revocando el refresh token."""
    use_case = LogoutUserUseCase()
    await use_case.execute(db, data.refresh_token)
    
    return create_success_response(
        message="Sesión cerrada exitosamente",
        data=None
    )


@router.post(
    "/change-password",
    response_model=SuccessResponse[None],
    summary="Cambiar contraseña",
    description="Cambia la contraseña del usuario autenticado"
)
async def change_password(
    data: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Cambia la contraseña del usuario autenticado."""
    use_case = ChangePasswordUseCase()
    await use_case.execute(
        db,
        current_user_id,
        data.current_password,
        data.new_password
    )
    
    return create_success_response(
        message="Contraseña cambiada exitosamente",
        data=None
    )


@router.post(
    "/request-password-reset",
    response_model=SuccessResponse[None],
    summary="Solicitar reset de contraseña",
    description="Envía email con token para resetear contraseña"
)
async def request_password_reset(
    data: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Solicita reset de contraseña (envía email con token)."""
    use_case = RequestPasswordResetUseCase()
    await use_case.execute(db, data.email)
    
    # Siempre retornar éxito (por seguridad, no revelar si el email existe)
    return create_success_response(
        message="Si el email existe, recibirás instrucciones para resetear tu contraseña",
        data=None
    )


@router.post(
    "/reset-password",
    response_model=SuccessResponse[None],
    summary="Resetear contraseña",
    description="Resetea la contraseña usando el token recibido por email"
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Resetea la contraseña usando token."""
    use_case = ResetPasswordUseCase()
    await use_case.execute(db, data.token, data.new_password)
    
    return create_success_response(
        message="Contraseña reseteada exitosamente",
        data=None
    )


@router.post(
    "/verify-email",
    response_model=SuccessResponse[None],
    summary="Verificar email",
    description="Verifica el email del usuario usando el token recibido"
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """Verifica el email del usuario."""
    use_case = VerifyEmailUseCase()
    await use_case.execute(db, data.token)
    
    return create_success_response(
        message="Email verificado exitosamente",
        data=None
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Obtener perfil actual",
    description="Retorna los datos del usuario autenticado"
)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """Obtiene el perfil del usuario autenticado."""
    usuario_repo = UsuarioRepository(db)
    #Estoy cambiando current_user_id a int(current_user_id)
    usuario = await usuario_repo.get_by_id(current_user_id)
    
    return create_success_response(
        message="Perfil obtenido exitosamente",
        data=usuario
    )


@router.patch(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Actualizar perfil",
    description="Actualiza el perfil del usuario autenticado"
)
async def update_profile(
    data: UpdateProfileRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """Actualiza el perfil del usuario."""
    usuario_repo = UsuarioRepository(db)
    usuario = await usuario_repo.get_by_id(current_user_id)
    
    # Actualizar campos
    if data.nombre is not None:
        usuario.nombre = data.nombre
    if data.telefono is not None:
        usuario.telefono = data.telefono
    
    usuario = await usuario_repo.update(usuario)
    
    return create_success_response(
        message="Perfil actualizado exitosamente",
        data=usuario
    )


@router.get(
    "/validate-token",
    response_model=TokenValidationResponse,
    summary="Validar token",
    description="Verifica si un access token es válido"
)
async def validate_token(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Valida un access token."""
    usuario_repo = UsuarioRepository(db)
    usuario = await usuario_repo.get_by_id(current_user_id)
    
    return TokenValidationResponse(
        valid=True,
        user_id=str(usuario.id),
        email=usuario.email,
        expires_at=None  # Se puede calcular del token si se necesita
    )
