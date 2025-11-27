"""
Modelos ORM para autenticación.
Define la estructura de datos de usuarios y tokens en la base de datos.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.shared.models import BaseModel


class RolUsuario(str, enum.Enum):
    """Roles de usuario en el sistema."""
    USER = "user"  # Minúsculas para coincidir con PostgreSQL ENUM
    ADMIN = "admin"  # Minúsculas para coincidir con PostgreSQL ENUM


class Usuario(BaseModel):
    """
    Modelo de Usuario del sistema.
    
    Attributes:
        email: Email único del usuario (usado para login)
        password_hash: Hash de la contraseña (bcrypt)
        nombre: Nombre completo del usuario
        telefono: Teléfono de contacto (opcional)
        email_verificado: Si el email ha sido verificado
        activo: Si la cuenta está activa
        es_admin: Si el usuario tiene permisos de administrador
        ultimo_login: Timestamp del último login
        motos: Relación con las motos del usuario
        suscripcion: Relación con la suscripción activa
        notificaciones: Relación con las notificaciones
        conversaciones: Relación con conversaciones del chatbot
    """
    
    __tablename__ = "usuarios"
    
    # Campos de autenticación
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Información personal
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    
    # Estado de la cuenta
    email_verificado = Column(Boolean, default=False, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    rol = Column(
        SQLEnum(RolUsuario, native_enum=True, name="rol_usuario", values_callable=lambda obj: [e.value for e in obj]),
        default=RolUsuario.USER,
        nullable=False,
        index=True
    )
    
    # Metadata de login
    ultimo_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    motos = relationship("Moto", back_populates="usuario", lazy="selectin")
    suscripcion = relationship("Suscripcion", back_populates="usuario", uselist=False, lazy="selectin")
    notificaciones = relationship("Notificacion", back_populates="usuario", lazy="selectin")
    conversaciones = relationship("Conversacion", back_populates="usuario", lazy="selectin")
    fallas_reportadas = relationship("Falla", back_populates="usuario", lazy="selectin")
    
    def __repr__(self):
        return f"<Usuario(email='{self.email}', nombre='{self.nombre}')>"
    
    def to_dict(self):
        """Convierte el usuario a diccionario (sin password_hash)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "telefono": self.telefono,
            "email_verificado": self.email_verificado,
            "activo": self.activo,
            "rol": self.rol.value if isinstance(self.rol, RolUsuario) else self.rol,
            "ultimo_login": self.ultimo_login.isoformat() if self.ultimo_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RefreshToken(BaseModel):
    """
    Modelo de Refresh Token para renovación de tokens JWT.
    
    Los refresh tokens permiten obtener nuevos access tokens sin re-autenticarse.
    Tienen mayor duración que los access tokens (30 días vs 1 hora).
    
    Attributes:
        usuario_id: ID del usuario propietario del token
        token: El refresh token único
        expires_at: Fecha de expiración
        revocado: Si el token ha sido revocado manualmente
        revocado_at: Timestamp de revocación (si aplica)
        ip_address: IP desde donde se generó el token
        user_agent: User agent del cliente
    """
    
    __tablename__ = "refresh_tokens"
    
    usuario_id = Column(Integer, nullable=False, index=True)
    token = Column(Text, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revocado = Column(Boolean, default=False, nullable=False)
    revocado_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata de seguridad
    ip_address = Column(String(45), nullable=True)  # IPv6 puede ser hasta 45 chars
    user_agent = Column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<RefreshToken(usuario_id='{self.usuario_id}', revocado={self.revocado})>"
    
    def is_valid(self) -> bool:
        """Verifica si el token es válido (no expirado ni revocado)."""
        if self.revocado:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True
    
    def to_dict(self):
        """Convierte el refresh token a diccionario."""
        return {
            "id": str(self.id),
            "usuario_id": self.usuario_id,
            "expires_at": self.expires_at.isoformat(),
            "revocado": self.revocado,
            "created_at": self.created_at.isoformat(),
        }


class PasswordResetToken(BaseModel):
    """
    Modelo de Token para reseteo de contraseña.
    
    Tokens de un solo uso para permitir a usuarios resetear su contraseña.
    Expiran en 1 hora.
    
    Attributes:
        usuario_id: ID del usuario que solicita el reset
        token: Token único de reseteo
        expires_at: Fecha de expiración (1 hora)
        usado: Si el token ya fue usado
        usado_at: Timestamp de uso
    """
    
    __tablename__ = "password_reset_tokens"
    
    usuario_id = Column(Integer, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    usado_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<PasswordResetToken(usuario_id='{self.usuario_id}', usado={self.usado})>"
    
    def is_valid(self) -> bool:
        """Verifica si el token es válido (no expirado ni usado)."""
        if bool(self.usado):
            return False
        # Asegúrate de que expires_at es un valor datetime, no un objeto Column
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def to_dict(self):
        """Convierte el token a diccionario."""
        return {
            "id": str(self.id),
            "usuario_id": self.usuario_id,
            "expires_at": self.expires_at.isoformat(),
            "usado": self.usado,
        }


class EmailVerificationToken(BaseModel):
    """
    Modelo de Token para verificación de email.
    
    Tokens enviados por email para verificar la propiedad del email.
    Expiran en 24 horas.
    
    Attributes:
        usuario_id: ID del usuario a verificar
        token: Token único de verificación
        expires_at: Fecha de expiración (24 horas)
        usado: Si el token ya fue usado
        usado_at: Timestamp de uso
    """
    
    __tablename__ = "email_verification_tokens"
    
    usuario_id = Column(Integer, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    usado_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<EmailVerificationToken(usuario_id='{self.usuario_id}', usado={self.usado})>"
    
    def is_valid(self) -> bool:
        """Verifica si el token es válido (no expirado ni usado)."""
        if self.usado:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True
    
    def to_dict(self):
        """Convierte el token a diccionario."""
        return {
            "id": str(self.id),
            "usuario_id": self.usuario_id,
            "expires_at": self.expires_at.isoformat(),
            "usado": self.usado,
        }
