"""
Módulo de autenticación.
Sistema completo de JWT, registro, login y gestión de usuarios.
"""

from .models import Usuario, RefreshToken, PasswordResetToken, EmailVerificationToken
from .schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    UpdateProfileRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    MessageResponse,
    TokenValidationResponse,
)
from .repositories import (
    UsuarioRepository,
    RefreshTokenRepository,
    PasswordResetTokenRepository,
    EmailVerificationTokenRepository,
)
from .services import (
    PasswordService,
    JWTService,
    AuthService,
    password_service,
    jwt_service,
    auth_service,
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
from .routes import router as auth_router
from . import events

__all__ = [
    # Models
    "Usuario",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    # Schemas
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "RequestPasswordResetRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "UpdateProfileRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "MessageResponse",
    "TokenValidationResponse",
    # Repositories
    "UsuarioRepository",
    "RefreshTokenRepository",
    "PasswordResetTokenRepository",
    "EmailVerificationTokenRepository",
    # Services
    "PasswordService",
    "JWTService",
    "AuthService",
    "password_service",
    "jwt_service",
    "auth_service",
    # Use Cases
    "RegisterUserUseCase",
    "LoginUserUseCase",
    "RefreshTokenUseCase",
    "LogoutUserUseCase",
    "ChangePasswordUseCase",
    "RequestPasswordResetUseCase",
    "ResetPasswordUseCase",
    "VerifyEmailUseCase",
    # Router
    "auth_router",
    # Events module (para acceder a eventos y emit functions)
    "events",
]
