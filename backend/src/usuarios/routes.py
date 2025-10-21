"""
Rutas de gestión de usuarios.
Endpoints para administración de usuarios (requiere permisos admin).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.dependencies import get_current_user_id, require_admin
from src.shared.base_models import (
    ApiResponse,
    SuccessResponse,
    PaginatedResponse,
    PaginationParams,
    create_paginated_response,
)
from .schemas import (
    CreateUsuarioRequest,
    UpdateUsuarioRequest,
    UsuarioFilterParams,
    UsuarioResponse,
    UsuarioStatsResponse,
)
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


router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[UsuarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def create_usuario(
    data: CreateUsuarioRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: str = Depends(get_current_user_id)
):
    """Crea un nuevo usuario."""
    use_case = CreateUsuarioUseCase()
    usuario = await use_case.execute(session, data, admin_id)
    return ApiResponse(
        success=True,
        message="Usuario creado exitosamente",
        data=usuario
    )


@router.get(
    "",
    response_model=PaginatedResponse[UsuarioResponse],
    summary="Listar usuarios",
    description="Lista usuarios con filtros y paginación (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def list_usuarios(
    filters: UsuarioFilterParams = Depends(),
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """Lista usuarios con filtros y paginación."""
    use_case = ListUsuariosUseCase()
    usuarios, total = await use_case.execute(session, filters, pagination)
    
    return create_paginated_response(
        message="Usuarios obtenidos exitosamente",
        data=usuarios,
        page=pagination.page,
        per_page=pagination.per_page,
        total_items=total
    )


@router.get(
    "/stats",
    response_model=ApiResponse[UsuarioStatsResponse],
    summary="Estadísticas de usuarios",
    description="Obtiene estadísticas generales de usuarios (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def get_usuario_stats(
    session: AsyncSession = Depends(get_db),
):
    """Obtiene estadísticas de usuarios."""
    use_case = GetUsuarioStatsUseCase()
    stats = await use_case.execute(session)
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=stats
    )


@router.get(
    "/{usuario_id}",
    response_model=ApiResponse[UsuarioResponse],
    summary="Obtener usuario",
    description="Obtiene un usuario por ID (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def get_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Obtiene un usuario por ID."""
    use_case = GetUsuarioUseCase()
    usuario = await use_case.execute(session, usuario_id)
    return ApiResponse(
        success=True,
        message="Usuario encontrado",
        data=usuario
    )


@router.patch(
    "/{usuario_id}",
    response_model=ApiResponse[UsuarioResponse],
    summary="Actualizar usuario",
    description="Actualiza un usuario existente (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def update_usuario(
    usuario_id: str,
    data: UpdateUsuarioRequest,
    session: AsyncSession = Depends(get_db),
    admin_id: str = Depends(get_current_user_id)
):
    """Actualiza un usuario."""
    use_case = UpdateUsuarioUseCase()
    usuario = await use_case.execute(session, usuario_id, data, admin_id)
    return ApiResponse(
        success=True,
        message="Usuario actualizado exitosamente",
        data=usuario
    )


@router.delete(
    "/{usuario_id}",
    response_model=SuccessResponse[None],
    summary="Eliminar usuario",
    description="Elimina un usuario (soft delete, requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def delete_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_db),
    admin_id: str = Depends(get_current_user_id)
):
    """Elimina un usuario (soft delete)."""
    use_case = DeleteUsuarioUseCase()
    await use_case.execute(session, usuario_id, admin_id)
    return SuccessResponse(
        message=f"Usuario {usuario_id} eliminado exitosamente",
        data=None
    )


@router.post(
    "/{usuario_id}/deactivate",
    response_model=SuccessResponse[None],
    summary="Desactivar usuario",
    description="Desactiva un usuario (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def deactivate_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_db),
    admin_id: str = Depends(get_current_user_id)
):
    """Desactiva un usuario."""
    use_case = DeactivateUsuarioUseCase()
    await use_case.execute(session, usuario_id, admin_id)
    return SuccessResponse(
        message=f"Usuario {usuario_id} desactivado exitosamente",
        data=None
    )


@router.post(
    "/{usuario_id}/activate",
    response_model=SuccessResponse[None],
    summary="Activar usuario",
    description="Activa un usuario (requiere permisos admin)",
    dependencies=[Depends(require_admin)]
)
async def activate_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_db),
    admin_id: str = Depends(get_current_user_id)
):
    """Activa un usuario."""
    use_case = ActivateUsuarioUseCase()
    await use_case.execute(session, usuario_id, admin_id)
    return SuccessResponse(
        message=f"Usuario {usuario_id} activado exitosamente",
        data=None
    )
