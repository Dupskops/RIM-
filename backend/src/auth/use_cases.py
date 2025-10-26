"""
Casos de uso de autenticación.
Orquesta la lógica de negocio de auth.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .models import Usuario, RefreshToken, PasswordResetToken, EmailVerificationToken
from .repositories import (
    UsuarioRepository,
    RefreshTokenRepository,
    PasswordResetTokenRepository,
    EmailVerificationTokenRepository,
)
from .services import password_service, jwt_service, auth_service
from .schemas import RegisterRequest, LoginRequest
from src.shared.exceptions import (
    UnauthorizedException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    ValidationException,
)
from . import events

logger = logging.getLogger(__name__)


class RegisterUserUseCase:
    """Caso de uso: Registrar nuevo usuario."""
    
    async def execute(
        self,
        session: AsyncSession,
        data: RegisterRequest,
        create_verification_token: bool = True
    ) -> Dict[str, Any]:
        """
        Registra un nuevo usuario.
        
        Args:
            session: Sesión de base de datos
            data: Datos de registro
            create_verification_token: Si crear token de verificación
            
        Returns:
            Diccionario con usuario y tokens
            
        Raises:
            ResourceAlreadyExistsException: Si el email ya existe
        """
        try:
            usuario_repo = UsuarioRepository(session)

            # Verificar que el email no exista
            if await usuario_repo.email_exists(data.email):
                raise ResourceAlreadyExistsException(
                    "Usuario",
                    f"El email {data.email} ya está registrado"
                )

            # Hashear contraseña (no loguear la contraseña)
            password_hash = password_service.hash_password(data.password)
            # Debug: no incluir el hash completo ni la contraseña
            try:
                logger.debug(
                    "Contraseña hasheada para email=%s (longitud_hash=%d)",
                    data.email,
                    len(password_hash),
                )
            except Exception:
                # En caso de que password_hash no sea indexable, evitar romper el flujo
                logger.debug("Se generó hash para email=%s", data.email)

            # Crear usuario
            usuario = Usuario(
                email=data.email,
                password_hash=password_hash,
                nombre=data.nombre,
                telefono=data.telefono,
                email_verificado=False,
                activo=True,
                rol="user",  # Todos los nuevos usuarios son "user" por defecto
            )

            usuario = await usuario_repo.create(usuario)
            logger.debug("Usuario creado id=%s email=%s", getattr(usuario, "id", None), getattr(usuario, "email", None))

            # Crear token de verificación si se solicita
            # verification_token = None
            if create_verification_token:
                token_repo = EmailVerificationTokenRepository(session)
                verification_token = EmailVerificationToken(
                    usuario_id=usuario.id,  # Mantener como integer
                    token=password_service.generate_verification_token(),
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                )
                # Si quiere imprimir el token de verificación para validar
                # print("Token de verificación creado:", verification_token)
                verification_token = await token_repo.create(verification_token)
                # No registrar el token en texto plano; solo metadatos
                logger.debug(
                    "Token de verificación creado para usuario_id=%s expira=%s",
                    getattr(verification_token, "usuario_id", None),
                    getattr(verification_token, "expires_at", None),
                )

            # Crear tokens JWT (el JWT usa string para el subject)
            tokens = auth_service.create_tokens(str(usuario.id), usuario.email)

            # Guardar refresh token en BD
            refresh_token_repo = RefreshTokenRepository(session)
            refresh_token_model = RefreshToken(
                usuario_id=usuario.id,  # Mantener como integer
                token=tokens["refresh_token"],
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            await refresh_token_repo.create(refresh_token_model)
            logger.debug(
                "Refresh token guardado para usuario_id=%s expira=%s",
                getattr(refresh_token_model, "usuario_id", None),
                getattr(refresh_token_model, "expires_at", None),
            )

            # Emitir evento
            await events.emit_user_registered(
                user_id=str(usuario.id),
                email=usuario.email,
                nombre=usuario.nombre,
                verification_token=verification_token.token if verification_token else None,
            )
            logger.debug("Evento 'usuario_registrado' emitido para usuario_id=%s", getattr(usuario, "id", None))

            logger.info("Usuario registrado: %s", usuario.email)

            return {
                "user": usuario,
                "tokens": tokens,
                "verification_token": verification_token.token if verification_token else None,
            }
        except ResourceAlreadyExistsException:
            # exceptions de negocio conocidas se propagan sin log de stacktrace
            raise
        except Exception:
            logger.exception("Error registrando usuario email=%s", data.email)
            raise


class LoginUserUseCase:
    """Caso de uso: Login de usuario."""
    
    async def execute(
        self,
        session: AsyncSession,
        data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Autentica un usuario.
        
        Args:
            session: Sesión de base de datos
            data: Datos de login
            ip_address: IP del cliente
            user_agent: User agent del cliente
            
        Returns:
            Diccionario con usuario y tokens
            
        Raises:
            UnauthorizedException: Si las credenciales son inválidas
        """
        usuario_repo = UsuarioRepository(session)
        
        # Buscar usuario por email
        usuario = await usuario_repo.get_by_email(data.email)
        if not usuario:
            logger.warning("Intento de login con email inexistente=%s", data.email)
            raise UnauthorizedException("Email o contraseña incorrectos")

        logger.debug("Usuario encontrado id=%s para email=%s", getattr(usuario, "id", None), data.email)
        
        # Verificar contraseña
        if not password_service.verify_password(data.password, usuario.password_hash):
            logger.warning("Intento de login fallido para email=%s desde ip=%s", data.email, ip_address)
            raise UnauthorizedException("Email o contraseña incorrectos")
        
        # Verificar que la cuenta esté activa
        if not usuario.activo:
            raise UnauthorizedException("Cuenta desactivada")
        
        # Actualizar último login
        await usuario_repo.update_ultimo_login(usuario.id)
        
        # Crear tokens JWT (el JWT usa string para el subject)
        tokens = auth_service.create_tokens(str(usuario.id), usuario.email)
        
        # Guardar refresh token en BD
        refresh_token_repo = RefreshTokenRepository(session)
        refresh_token_model = RefreshToken(
            usuario_id=usuario.id,  # Mantener como integer
            token=tokens["refresh_token"],
            expires_at=datetime.utcnow() + timedelta(days=30),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await refresh_token_repo.create(refresh_token_model)
        logger.debug(
            "Refresh token de login guardado para usuario_id=%s expira=%s",
            getattr(refresh_token_model, "usuario_id", None),
            getattr(refresh_token_model, "expires_at", None),
        )
        
        # Emitir evento
        await events.emit_user_logged_in(
            user_id=str(usuario.id),
            email=usuario.email,
            ip_address=ip_address,
        )
        
        logger.info(f"Usuario autenticado: {usuario.email}")
        
        return {
            "user": usuario,
            "tokens": tokens,
        }


class RefreshTokenUseCase:
    """Caso de uso: Renovar access token."""
    
    async def execute(
        self,
        session: AsyncSession,
        refresh_token: str
    ) -> Dict[str, str]:
        """
        Renueva el access token usando refresh token.
        
        Args:
            session: Sesión de base de datos
            refresh_token: Refresh token
            
        Returns:
            Nuevo access token
            
        Raises:
            UnauthorizedException: Si el refresh token es inválido
        """
        # Verificar refresh token JWT
        payload = jwt_service.verify_refresh_token(refresh_token)
        #Cambien user_id = payload["user_id"] por user_id = payload.get("user_id") or payload.get("sub")

        user_id = payload.get("user_id") or payload.get("sub")

        
        # Verificar que el token exista en BD y esté válido
        token_repo = RefreshTokenRepository(session)
        token_model = await token_repo.get_by_token(refresh_token)
        
        if not token_model or not token_model.is_valid():
            raise UnauthorizedException("Refresh token inválido o expirado")
        
        # Obtener usuario
        usuario_repo = UsuarioRepository(session)
        usuario = await usuario_repo.get_by_id(user_id)
        logger.debug("Búsqueda por refresh token: user_id=%s -> usuario=%s", user_id, getattr(usuario, "id", None))

        if not usuario or not usuario.activo:
            logger.warning("Token de actualización rechazado por user_id=%s (No encontrado o inactivo)", user_id)
            raise UnauthorizedException("Usuario no encontrado o inactivo")
        
        # Crear nuevo access token
        new_access_token = jwt_service.create_access_token({
            "user_id": str(usuario.id),
            "email": usuario.email,
        })
        
        logger.info(f"Access token renovado para usuario: {usuario.email}")
        #Coloque el campo refresh_Token 
        return {
            "access_token": new_access_token,
            "refresh_token":refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }


class LogoutUserUseCase:
    """Caso de uso: Logout de usuario."""
    
    async def execute(
        self,
        session: AsyncSession,
        refresh_token: str
    ) -> None:
        """
        Cierra sesión revocando el refresh token.
        
        Args:
            session: Sesión de base de datos
            refresh_token: Refresh token a revocar
        """
        token_repo = RefreshTokenRepository(session)
        await token_repo.revoke_token(refresh_token)
        
        logger.info("Usuario cerró sesión")


class ChangePasswordUseCase:
    """Caso de uso: Cambiar contraseña."""
    
    async def execute(
        self,
        session: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Cambia la contraseña de un usuario autenticado.
        
        Args:
            session: Sesión de base de datos
            user_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Raises:
            UnauthorizedException: Si la contraseña actual es incorrecta
        """
        logger.debug("Solicitud de cambio de contraseña para usuario_id=%s", user_id)
        usuario_repo = UsuarioRepository(session)
        usuario = await usuario_repo.get_by_id(user_id)

        if not usuario:
            raise ResourceNotFoundException("Usuario", user_id)

        # Verificar contraseña actual
        if not password_service.verify_password(current_password, usuario.password_hash):
            raise UnauthorizedException("Contraseña actual incorrecta")

        # Hashear nueva contraseña
        new_password_hash = password_service.hash_password(new_password)
        logger.debug(
            "Nueva contraseña hasheada para usuario_id=%s (longitud_hash=%d)",
            user_id,
            len(new_password_hash),
        )

        # Actualizar contraseña
        await usuario_repo.update_password(user_id, new_password_hash)
        logger.debug("Contraseña actualizada para usuario_id=%s", user_id)

        # Revocar todos los refresh tokens (forzar re-login)
        token_repo = RefreshTokenRepository(session)
        await token_repo.revoke_all_user_tokens(user_id)

        # Emitir evento
        await events.emit_password_changed(
            user_id=user_id,
            email=usuario.email,
        )

        logger.info(f"Contraseña cambiada para usuario: {usuario.email}")


class RequestPasswordResetUseCase:
    """Caso de uso: Solicitar reset de contraseña."""
    
    async def execute(
        self,
        session: AsyncSession,
        email: str
    ) -> Optional[str]:
        """
        Genera token de reset y lo devuelve (para enviar por email).
        
        Args:
            session: Sesión de base de datos
            email: Email del usuario
            
        Returns:
            Token de reset (o None si el email no existe - por seguridad no revelar)
        """
        try:
            usuario_repo = UsuarioRepository(session)
            usuario = await usuario_repo.get_by_email(email)

            # Por seguridad, no revelar si el email existe o no
            if not usuario:
                logger.warning("Intento de reset para email no existente: %s", email)
                raise ResourceNotFoundException("Usuario", email)

            # Generar token (no registrar el token en texto plano)
            reset_token = password_service.generate_reset_token()
            logger.debug("Generando token de restablecimiento de contraseña para usuario_id=%s", getattr(usuario, "id", None))
            # Guardar en BD
            token_repo = PasswordResetTokenRepository(session)
            token_model = PasswordResetToken(
                usuario_id=usuario.id,
                token=reset_token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )
            await token_repo.create(token_model)
            logger.debug(
                "Token de restablecimiento de contraseña guardado para usuario_id=%s expira=%s",
                getattr(token_model, "usuario_id", None),
                getattr(token_model, "expires_at", None),
            )

            # Emitir evento (para enviar email)
            await events.emit_password_reset_requested(
                user_id=str(usuario.id),
                email=usuario.email,
                reset_token=reset_token,
            )

            logger.info("Token de restablecimiento de contraseña generado para: %s", email)

            return reset_token
        except Exception:
            # Log con stacktrace para diagnóstico y relanzar
            logger.exception("Error solicitando restablecimiento de contraseña para email=%s", email)
            raise


class ResetPasswordUseCase:
    """Caso de uso: Resetear contraseña con token."""

    async def execute(
        self,
        session: AsyncSession,
        token: str,
        new_password: str,
    ) -> None:
        """
        Resetea la contraseña usando token.

        Args:
            session: Sesión de base de datos
            token: Token de reset
            new_password: Nueva contraseña

        Raises:
            ValidationException: Si el token es inválido
        """
        token_repo = PasswordResetTokenRepository(session)
        token_model = await token_repo.get_by_token(token)
        if not token_model or not token_model.is_valid():
            logger.warning("Token de restablecimiento de contraseña inválido o expirado usado")
            raise ValidationException("Token de restablecimiento de contraseña inválido o expirado")

        # Hashear nueva contraseña
        new_password_hash = password_service.hash_password(new_password)
        logger.debug(
            "Restableciendo contraseña para usuario_id=%s",
            getattr(token_model, "usuario_id", None),
        )

        # Actualizar contraseña
        usuario_repo = UsuarioRepository(session)
        await usuario_repo.update_password(token_model.usuario_id, new_password_hash)

        # Marcar token como usado
        await token_repo.mark_as_used(token)
        logger.debug(
            "Token de restablecimiento de contraseña marcado como usado para usuario_id=%s",
            getattr(token_model, "usuario_id", None),
        )

        # Revocar todos los refresh tokens
        refresh_token_repo = RefreshTokenRepository(session)
        await refresh_token_repo.revoke_all_user_tokens(token_model.usuario_id)

        # Emitir evento
        await events.emit_password_reset_completed(
            user_id=str(token_model.usuario_id),
        )

        logger.info(f"Contraseña restablecida para usuario: {token_model.usuario_id}")


class VerifyEmailUseCase:
    """Caso de uso: Verificar email."""
    
    async def execute(
        self,
        session: AsyncSession,
        token: str
    ) -> None:
        """
        Verifica el email de un usuario.
        
        Args:
            session: Sesión de base de datos
            token: Token de verificación
            
        Raises:
            ValidationException: Si el token es inválido
        """
        token_repo = EmailVerificationTokenRepository(session)
        token_model = await token_repo.get_by_token(token)
        
        if not token_model or not token_model.is_valid():
            raise ValidationException("Token de verificación inválido o expirado")
        
        # Marcar email como verificado
        usuario_repo = UsuarioRepository(session)
        await usuario_repo.verify_email(token_model.usuario_id)
        logger.debug("Verificación de email aplicada para usuario_id=%s", getattr(token_model, "usuario_id", None))

        # Marcar token como usado
        await token_repo.mark_as_used(token)

        # Emitir evento
        await events.emit_email_verified(
            user_id=token_model.usuario_id,
        )

        logger.info(f"Email verificado para usuario: {token_model.usuario_id}")
