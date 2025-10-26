"""
Repositorios para gestión de usuarios.
Maneja acceso a base de datos para usuarios.
"""
from typing import List, Optional, Tuple, Union
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from src.auth.models import Usuario

# Logger para el repositorio de usuarios
logger = logging.getLogger(__name__)


class UsuarioRepository:
    """Repositorio para operaciones de usuario (admin CRUD)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, usuario_id: Union[int, str]) -> Optional[Usuario]:
        """Obtiene usuario por ID.

        Acepta int o str; si recibe str intenta convertir a int para evitar
        errores de tipo al ejecutar la consulta en PostgreSQL.
        """
        try:
            # Asegurar que el parámetro usado en la consulta sea un entero
            if isinstance(usuario_id, str):
                try:
                    usuario_id = int(usuario_id)
                except (ValueError, TypeError):
                    logger.exception("ID de usuario inválido: %s", usuario_id)
                    raise ValueError("usuario_id must be an integer")

            result = await self.session.execute(
                select(Usuario).where(
                    and_(
                        Usuario.id == usuario_id,
                        Usuario.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            # Loguear con stacktrace para saber exactamente por qué falló
            logger.exception("Error al obtener usuario por id=%s", usuario_id)
            # Relanzar para que la capa superior decida cómo manejarlo
            raise
    
    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtiene usuario por email."""
        result = await self.session.execute(
            select(Usuario).where(
                and_(
                    Usuario.email == email,
                    Usuario.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_usuarios(
        self,
        query: Optional[str] = None,
        rol: Optional[str] = None,
        activo: Optional[bool] = None,
        email_verificado: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Usuario], int]:
        """
        Lista usuarios con filtros y paginación.
        
        Returns:
            Tupla de (lista_usuarios, total_count)
        """
        # Construir query base
        conditions = [Usuario.deleted_at.is_(None)]
        
        # Filtro de búsqueda por nombre o email
        if query:
            search_term = f"%{query}%"
            conditions.append(
                or_(
                    Usuario.nombre.ilike(search_term),
                    Usuario.email.ilike(search_term)
                )
            )
        
        # Filtros específicos
        if rol is not None:
            conditions.append(Usuario.rol == rol)
        
        if activo is not None:
            conditions.append(Usuario.activo == activo)
        
        if email_verificado is not None:
            conditions.append(Usuario.email_verificado == email_verificado)
        
        # Query de usuarios
        stmt = select(Usuario).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        usuarios = result.scalars().all()
        
        # Query de conteo
        count_stmt = select(func.count(Usuario.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()
        
        return list(usuarios), total
    
    async def create(self, usuario: Usuario) -> Usuario:
        """Crea un nuevo usuario."""
        self.session.add(usuario)
        await self.session.flush()
        await self.session.refresh(usuario)
        return usuario
    
    async def update(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario existente."""
        usuario.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(usuario)
        return usuario
    
    async def delete(self, usuario_id: str) -> bool:
        """
        Soft delete de usuario.
        
        Returns:
            True si se eliminó, False si no existe
        """
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            return False
        
        usuario.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True
    
    async def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verifica si un email ya existe.
        
        Args:
            email: Email a verificar
            exclude_id: ID de usuario a excluir (para updates)
        """
        conditions = [
            Usuario.email == email,
            Usuario.deleted_at.is_(None)
        ]
        
        if exclude_id:
            conditions.append(Usuario.id != exclude_id)
        
        result = await self.session.execute(
            select(func.count(Usuario.id)).where(and_(*conditions))
        )
        return result.scalar_one() > 0
    
    async def count_usuarios(
        self,
        activo: Optional[bool] = None,
        email_verificado: Optional[bool] = None,
        rol: Optional[str] = None
    ) -> int:
        """Cuenta usuarios con filtros opcionales."""
        conditions = [Usuario.deleted_at.is_(None)]
        
        if activo is not None:
            conditions.append(Usuario.activo == activo)
        
        if email_verificado is not None:
            conditions.append(Usuario.email_verificado == email_verificado)
        
        if rol is not None:
            conditions.append(Usuario.rol == rol)
        
        result = await self.session.execute(
            select(func.count(Usuario.id)).where(and_(*conditions))
        )
        return result.scalar_one()
    
    async def count_recent_usuarios(self, days: int = 7) -> int:
        """Cuenta usuarios registrados en los últimos N días."""
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            select(func.count(Usuario.id)).where(
                and_(
                    Usuario.created_at >= since,
                    Usuario.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one()
    
    async def deactivate_usuario(self, usuario_id: str) -> bool:
        """
        Desactiva un usuario.
        
        Returns:
            True si se desactivó, False si no existe
        """
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            return False
        
        usuario.activo = False
        usuario.updated_at = datetime.utcnow()
        await self.session.flush()
        return True
    
    async def activate_usuario(self, usuario_id: int) -> bool:
        """
        Activa un usuario.
        
        Returns:
            True si se activó, False si no existe
        """
        usuario = await self.get_by_id(usuario_id)
        if not usuario:
            return False
        
        usuario.activo = True
        usuario.updated_at = datetime.utcnow()
        await self.session.flush()
        return True
