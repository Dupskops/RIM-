"""
Repositorios para acceso a datos de autenticación.
Capa de acceso a datos para usuarios y tokens.
"""
from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging

from .models import Usuario, RefreshToken, PasswordResetToken, EmailVerificationToken

logger = logging.getLogger(__name__)


class UsuarioRepository:
    """Repositorio para operaciones de Usuario."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
    
    async def create(self, usuario: Usuario) -> Usuario:
        """Crea un nuevo usuario."""
        self.session.add(usuario)
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario

   #Cambie el get_by_id - Usuario.id == user_id) para hacer la conversion a INT 
    async def get_by_id(self, user_id) -> Optional[Usuario]:
        """Obtiene usuario por ID."""
        try:   
            user_id = int(user_id)
        except (TypeError, ValueError):
            logger.warning(f"ID de usuario inválido recibido: {user_id}")
            return None    
                
        result = await self.session.execute(
            select(Usuario).where(Usuario.id == int(user_id))
        )
        return result.scalar_one_or_none()



    async def get_by_email(self, email: str) -> Optional[Usuario]:
        """Obtiene usuario por email."""
        try:
            result = await self.session.execute(
                select(Usuario).where(Usuario.email == email)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Error al obtener usuario por email=%s", email)
            raise
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = None
    ) -> List[Usuario]:
        """Obtiene lista de usuarios con paginación."""
        query = select(Usuario).offset(skip).limit(limit)
        
        if activo is not None:
            query = query.where(Usuario.activo == activo)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario."""
        await self.session.commit()
        await self.session.refresh(usuario)
        return usuario
    
    async def update_ultimo_login(self, user_id: int) -> None:
        """Actualiza el timestamp de último login."""
        await self.session.execute(
            update(Usuario)
            .where(Usuario.id == user_id)
            .values(ultimo_login=datetime.utcnow())
        )
        await self.session.commit()
    #Coloque user_id por int(user_id)
    async def update_password(self, user_id: int, password_hash: str) -> None:
        """Actualiza la contraseña de un usuario."""
        await self.session.execute(
            update(Usuario)
            .where(Usuario.id == int(user_id))
            .values(password_hash=password_hash)
        )
        await self.session.commit()
    
    async def verify_email(self, user_id: int) -> None:
        """Marca el email del usuario como verificado."""
        await self.session.execute(
            update(Usuario)
            .where(Usuario.id == user_id)
            .values(email_verificado=True)
        )
        await self.session.commit()
    
    async def deactivate(self, user_id: int) -> None:
        """Desactiva una cuenta de usuario."""
        await self.session.execute(
            update(Usuario)
            .where(Usuario.id == user_id)
            .values(activo=False)
        )
        await self.session.commit()
    
    async def delete(self, user_id: int) -> None:
        """Elimina un usuario (soft delete si BaseModel lo soporta)."""
        await self.session.execute(
            delete(Usuario).where(Usuario.id == user_id)
        )
        await self.session.commit()
    
    async def email_exists(self, email: str) -> bool:
        """Verifica si un email ya está registrado."""
        result = await self.session.execute(
            select(Usuario.id).where(Usuario.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def count_admins(self) -> int:
        """Cuenta cuántos administradores existen."""
        result = await self.session.execute(
            select(Usuario.id).where(Usuario.rol == "admin")
        )
        return len(list(result.scalars().all()))


class RefreshTokenRepository:
    """Repositorio para operaciones de RefreshToken."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio.
        
        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
    
    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        """Crea un nuevo refresh token."""
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token
    
    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Obtiene refresh token por su valor."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> List[RefreshToken]:
        """Obtiene todos los refresh tokens de un usuario."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.usuario_id == user_id)
        )
        return list(result.scalars().all())
    
    async def revoke_token(self, token: str) -> None:
        """Revoca un refresh token."""
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(revocado=True, revocado_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoca todos los tokens de un usuario."""
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == user_id)
            .values(revocado=True, revocado_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def delete_expired(self) -> int:
        """Elimina tokens expirados. Retorna cantidad eliminada."""
        result = await self.session.execute(
            delete(RefreshToken)
            .where(RefreshToken.expires_at < datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount


class PasswordResetTokenRepository:
    """Repositorio para tokens de reseteo de contraseña."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Crea un nuevo token de reseteo."""
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token
    
    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Obtiene token por su valor."""
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        return result.scalar_one_or_none()
    
    async def mark_as_used(self, token: str) -> None:
        """Marca un token como usado."""
        await self.session.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .values(usado=True, usado_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def delete_expired(self) -> int:
        """Elimina tokens expirados."""
        result = await self.session.execute(
            delete(PasswordResetToken)
            .where(PasswordResetToken.expires_at < datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount


class EmailVerificationTokenRepository:
    """Repositorio para tokens de verificación de email."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        """Crea un nuevo token de verificación."""
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token
    
    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Obtiene token por su valor."""
        result = await self.session.execute(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token == token)
        )
        return result.scalar_one_or_none()
    
    async def mark_as_used(self, token: str) -> None:
        """Marca un token como usado."""
        await self.session.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.token == token)
            .values(usado=True, usado_at=datetime.utcnow())
        )
        await self.session.commit()
    
    async def delete_expired(self) -> int:
        """Elimina tokens expirados."""
        result = await self.session.execute(
            delete(EmailVerificationToken)
            .where(EmailVerificationToken.expires_at < datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount
