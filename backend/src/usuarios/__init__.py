"""
Módulo de gestión de usuarios.
Sistema de administración de usuarios (CRUD, búsqueda, estadísticas).
"""

from .models import Usuario
from .schemas import (
    CreateUsuarioRequest,
    UpdateUsuarioRequest,
    #SearchUsuariosRequest,
    UsuarioResponse,
    #UsuarioListResponse,
    UsuarioStatsResponse,
    #MessageResponse,
)
from .repositories import UsuarioRepository
from .services import usuario_service, UsuarioService
from .use_cases import (
    CreateUsuarioUseCase,
    GetUsuarioUseCase,
    ListUsuariosUseCase,
    UpdateUsuarioUseCase,
    DeleteUsuarioUseCase,
    DeactivateUsuarioUseCase,
    ActivateUsuarioUseCase,
    GetUsuarioStatsUseCase,
)
from .routes import router as usuarios_router
from . import events

__all__ = [
    # Models
    "Usuario",
    # Schemas
    "CreateUsuarioRequest",
    "UpdateUsuarioRequest",
    #"SearchUsuariosRequest",
    "UsuarioResponse",
    #"UsuarioListResponse",
    "UsuarioStatsResponse",
    #"MessageResponse",
    # Repositories
    "UsuarioRepository",
    # Services
    "UsuarioService",
    "usuario_service",
    # Use Cases
    "CreateUsuarioUseCase",
    "GetUsuarioUseCase",
    "ListUsuariosUseCase",
    "UpdateUsuarioUseCase",
    "DeleteUsuarioUseCase",
    "DeactivateUsuarioUseCase",
    "ActivateUsuarioUseCase",
    "GetUsuarioStatsUseCase",
    # Router
    "usuarios_router",
    # Events module
    "events",
]
