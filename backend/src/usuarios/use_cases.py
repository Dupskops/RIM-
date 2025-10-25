"""
Casos de uso de gestión de usuarios.
Orquesta la lógica de negocio de administración de usuarios.
"""
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.auth.models import Usuario
from .repositories import UsuarioRepository
from .services import usuario_service
from .schemas import (
    CreateUsuarioRequest,
    UpdateUsuarioRequest,
    UsuarioFilterParams,
)
from src.shared.base_models import PaginationParams
from src.shared.exceptions import (
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
)
from . import events

logger = logging.getLogger(__name__)


class CreateUsuarioUseCase:
    """Caso de uso: Crear usuario (admin only)."""
    
    async def execute(
        self,
        session: AsyncSession,
        data: CreateUsuarioRequest,
        admin_id: str
    ) -> Usuario:
        """
        Crea un nuevo usuario.
        
        Args:
            session: Sesión de base de datos
            data: Datos del usuario a crear
            admin_id: ID del admin que crea el usuario
            
        Returns:
            Usuario creado
            
        Raises:
            ResourceAlreadyExistsException: Si el email ya existe
        """
        repo = UsuarioRepository(session)
        
        # Verificar que el email no exista
        if await repo.email_exists(data.email):
            raise ResourceAlreadyExistsException(
                "Usuario",
                f"El email {data.email} ya está registrado"
            )
        
        # Preparar datos
        usuario_data = usuario_service.prepare_usuario_data(
            email=data.email,
            password=data.password,
            nombre=data.nombre,
            telefono=data.telefono,
            es_admin=data.es_admin,
            activo=data.activo,
        )
        
        # Crear usuario
        usuario = Usuario(**usuario_data)
        usuario = await repo.create(usuario)
        
        # Emitir evento
        await events.emit_usuario_created(
            usuario_id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            created_by_admin_id=admin_id,
        )
        
        logger.info(f"Usuario creado por admin {admin_id}: {usuario.email}")
        
        return usuario


class GetUsuarioUseCase:
    """Caso de uso: Obtener usuario por ID."""
    
    async def execute(
        self,
        session: AsyncSession,
        usuario_id: str
    ) -> Usuario:
        """
        Obtiene un usuario por su ID.
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario encontrado
            
        Raises:
            ResourceNotFoundException: Si el usuario no existe
        """
        repo = UsuarioRepository(session)
        usuario = await repo.get_by_id(usuario_id)
        
        if not usuario:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        return usuario


class ListUsuariosUseCase:
    """Caso de uso: Listar usuarios con filtros."""
    
    async def execute(
        self,
        session: AsyncSession,
        filters: UsuarioFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Usuario], int]:
        """
        Lista usuarios con filtros y paginación.
        
        Args:
            session: Sesión de base de datos
            filters: Filtros de búsqueda
            pagination: Parámetros de paginación
            
        Returns:
            Tupla con lista de usuarios y total
        """
        repo = UsuarioRepository(session)
        
        # Obtener usuarios con los parámetros actualizados
        usuarios, total = await repo.list_usuarios(
            query=filters.search,  # Renombrado de query a search
            #CAMBIEN es_admin por rol
            rol=filters.rol,
            activo=filters.activo,
            email_verificado=filters.email_verificado,
            skip=pagination.offset,
            limit=pagination.limit
        )
        
        return usuarios, total


class UpdateUsuarioUseCase:
    """Caso de uso: Actualizar usuario (admin only)."""
    
    async def execute(
        self,
        session: AsyncSession,
        usuario_id: str,
        data: UpdateUsuarioRequest,
        admin_id: str
    ) -> Usuario:
        """
        Actualiza un usuario existente.
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario a actualizar
            data: Datos a actualizar
            admin_id: ID del admin que actualiza
            
        Returns:
            Usuario actualizado
            
        Raises:
            ResourceNotFoundException: Si el usuario no existe
        """
        repo = UsuarioRepository(session)
        usuario = await repo.get_by_id(usuario_id)
        
        if not usuario:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Rastrear cambios para evento
        changes = {}
        
        # Actualizar campos
        if data.nombre is not None and data.nombre != usuario.nombre:
            changes["nombre"] = {"old": usuario.nombre, "new": data.nombre}
            usuario.nombre = data.nombre  # type: ignore
        
        if data.telefono is not None and data.telefono != usuario.telefono:
            changes["telefono"] = {"old": usuario.telefono, "new": data.telefono}
            usuario.telefono = data.telefono  # type: ignore
        
        if data.es_admin is not None and data.es_admin != usuario.es_admin:
            changes["es_admin"] = {"old": usuario.es_admin, "new": data.es_admin}
            usuario.es_admin = data.es_admin  # type: ignore
        
        if data.activo is not None and data.activo != usuario.activo:
            changes["activo"] = {"old": usuario.activo, "new": data.activo}
            usuario.activo = data.activo  # type: ignore
        
        # Guardar cambios
        usuario = await repo.update(usuario)
        
        # Emitir evento si hubo cambios
        if changes:
            await events.emit_usuario_updated(
                usuario_id=str(usuario.id),
                email=usuario.email,
                updated_by_admin_id=admin_id,
                changes=changes,
            )
            
            logger.info(
                f"Usuario {usuario.email} actualizado por admin {admin_id}. "
                f"Cambios: {list(changes.keys())}"
            )
        
        return usuario


class DeleteUsuarioUseCase:
    """Caso de uso: Eliminar usuario (soft delete)."""
    
    async def execute(
        self,
        session: AsyncSession,
        usuario_id: str,
        admin_id: str
    ) -> None:
        """
        Elimina un usuario (soft delete).
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario a eliminar
            admin_id: ID del admin que elimina
            
        Raises:
            ResourceNotFoundException: Si el usuario no existe
        """
        repo = UsuarioRepository(session)
        
        # Obtener usuario primero para validar y obtener email
        usuario = await repo.get_by_id(usuario_id)
        if not usuario:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Eliminar
        await repo.delete(usuario_id)
        
        # Emitir evento
        await events.emit_usuario_deleted(
            usuario_id=usuario_id,
            email=usuario.email,
            deleted_by_admin_id=admin_id,
        )
        
        logger.info(f"Usuario {usuario.email} eliminado por admin {admin_id}")


class DeactivateUsuarioUseCase:
    """Caso de uso: Desactivar usuario."""
    
    async def execute(
        self,
        session: AsyncSession,
        usuario_id: str,
        admin_id: str
    ) -> None:
        """
        Desactiva un usuario.
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario a desactivar
            admin_id: ID del admin que desactiva
            
        Raises:
            ResourceNotFoundException: Si el usuario no existe
        """
        repo = UsuarioRepository(session)
        
        # Obtener usuario para validar y obtener email
        usuario = await repo.get_by_id(usuario_id)
        if not usuario:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Desactivar
        success = await repo.deactivate_usuario(usuario_id)
        if not success:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Emitir evento
        await events.emit_usuario_deactivated(
            usuario_id=usuario_id,
            email=usuario.email,
            deactivated_by_admin_id=admin_id,
        )
        
        logger.info(f"Usuario {usuario.email} desactivado por admin {admin_id}")


class ActivateUsuarioUseCase:
    """Caso de uso: Activar usuario."""
    
    async def execute(
        self,
        session: AsyncSession,
        usuario_id: str,
        admin_id: str
    ) -> None:
        """
        Activa un usuario.
        
        Args:
            session: Sesión de base de datos
            usuario_id: ID del usuario a activar
            admin_id: ID del admin que activa
            
        Raises:
            ResourceNotFoundException: Si el usuario no existe
        """
        repo = UsuarioRepository(session)
        
        # Obtener usuario para validar y obtener email
        usuario = await repo.get_by_id(usuario_id)
        if not usuario:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Activar
        success = await repo.activate_usuario(usuario_id)
        if not success:
            raise ResourceNotFoundException("Usuario", usuario_id)
        
        # Emitir evento
        await events.emit_usuario_activated(
            usuario_id=usuario_id,
            email=usuario.email,
            activated_by_admin_id=admin_id,
        )
        
        logger.info(f"Usuario {usuario.email} activado por admin {admin_id}")


class GetUsuarioStatsUseCase:
    """Caso de uso: Obtener estadísticas de usuarios."""
    
    async def execute(
        self,
        session: AsyncSession
    ) -> Dict[str, int]:
        """
        Obtiene estadísticas generales de usuarios.
        
        Args:
            session: Sesión de base de datos
            
        Returns:
            Diccionario con estadísticas
        """
        repo = UsuarioRepository(session)
        
        # Obtener conteos
        total_usuarios = await repo.count_usuarios()
        usuarios_activos = await repo.count_usuarios(activo=True)
        usuarios_inactivos = await repo.count_usuarios(activo=False)
        emails_verificados = await repo.count_usuarios(email_verificado=True)
        emails_sin_verificar = await repo.count_usuarios(email_verificado=False)
        administradores = await repo.count_usuarios(es_admin=True)
        usuarios_recientes = await repo.count_recent_usuarios(days=7)
        
        return {
            "total_usuarios": total_usuarios,
            "usuarios_activos": usuarios_activos,
            "usuarios_inactivos": usuarios_inactivos,
            "emails_verificados": emails_verificados,
            "emails_sin_verificar": emails_sin_verificar,
            "administradores": administradores,
            "usuarios_recientes": usuarios_recientes,
        }
