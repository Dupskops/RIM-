"""
Servicios de autenticación.
Maneja JWT, hashing de contraseñas y lógica de autenticación.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import jwt
from passlib.context import CryptContext
import logging

from src.config.settings import settings
from src.shared.exceptions import (
    UnauthorizedException,
    ValidationException,
)

logger = logging.getLogger(__name__)

# Importar bcrypt directamente
import bcrypt

# Configuración de bcrypt para hashing de contraseñas
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
)

# Forzar el backend de bcrypt para evitar el bug de detección
try:
    from passlib.handlers.bcrypt import _BcryptCommon
    _BcryptCommon._finalize_backend_mixin = lambda *args, **kwargs: None
except:
    pass


class PasswordService:
    """Servicio para manejo de contraseñas."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Genera hash de contraseña usando bcrypt.
        
        Bcrypt tiene un límite de 72 bytes. Las contraseñas más largas
        se truncan automáticamente.
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        # Usar bcrypt directamente para evitar problemas con passlib
        password_bytes = password.encode('utf-8')
        
        # Bcrypt solo acepta hasta 72 bytes
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generar salt y hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica que la contraseña coincida con el hash.
        
        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash almacenado
            
        Returns:
            True si la contraseña es correcta
        """
        # Usar bcrypt directamente
        password_bytes = plain_password.encode('utf-8')
        
        # Truncar si excede 72 bytes (igual que en hash_password)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def generate_reset_token() -> str:
        """
        Genera un token seguro para reset de contraseña.
        
        Returns:
            Token aleatorio de 32 bytes en hexadecimal
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Genera un token seguro para verificación de email.
        
        Returns:
            Token aleatorio de 32 bytes en hexadecimal
        """
        return secrets.token_urlsafe(32)


class JWTService:
    """Servicio para manejo de JWT tokens."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un access token JWT.
        
        Args:
            data: Datos a incluir en el token (típicamente user_id, email)
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        # Calcular expiración
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        # Agregar claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        # Codificar token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un refresh token JWT.
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración personalizado
            
        Returns:
            Refresh token JWT codificado
        """
        to_encode = data.copy()
        
        # Calcular expiración (30 días por defecto)
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        # Agregar claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        # Codificar token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decodifica y valida un JWT token.
        
        Args:
            token: Token JWT a decodificar
            
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
            
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token expirado")
        except jwt.InvalidSignatureError:
            raise UnauthorizedException("Token inválido")
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """
        Verifica que sea un access token válido.
        
        Args:
            token: Access token a verificar
            
        Returns:
            Payload del token
            
        Raises:
            UnauthorizedException: Si no es un access token válido
        """
        payload = JWTService.decode_token(token)
        
        # Verificar que sea un access token
        if payload.get("type") != "access":
            raise UnauthorizedException("Token tipo incorrecto")
        
        # Verificar que tenga sub (user_id)
        if "sub" not in payload:
            raise UnauthorizedException("Token inválido: falta user_id")
        
        return payload
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """
        Verifica que sea un refresh token válido.
        
        Args:
            token: Refresh token a verificar
            
        Returns:
            Payload del token
            
        Raises:
            UnauthorizedException: Si no es un refresh token válido
        """
        payload = JWTService.decode_token(token)
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Token tipo incorrecto")
        
        # Verificar que tenga sub (user_id)
        if "sub" not in payload:
            raise UnauthorizedException("Token inválido: falta user_id")
        
        return payload
    
    @staticmethod
    def get_token_expiration(token: str) -> datetime:
        """
        Obtiene la fecha de expiración de un token.
        
        Args:
            token: Token JWT
            
        Returns:
            Fecha de expiración
        """
        payload = JWTService.decode_token(token)
        exp_timestamp = payload.get("exp")
        
        if not exp_timestamp:
            raise ValidationException("Token sin fecha de expiración")
        
        return datetime.fromtimestamp(exp_timestamp)


class AuthService:
    """Servicio principal de autenticación."""
    
    def __init__(self):
        """Inicializa el servicio de autenticación."""
        self.password_service = PasswordService()
        self.jwt_service = JWTService()
    
    def create_tokens(self, user_id: str, email: str) -> Dict[str, Any]:
        """
        Crea access token y refresh token para un usuario.
        
        Args:
            user_id: ID del usuario
            email: Email del usuario
            
        Returns:
            Diccionario con access_token, refresh_token, token_type, expires_in
        """
        # Datos para los tokens (usar "sub" como estándar JWT para user_id)
        token_data = {
            "sub": str(user_id),  # "sub" (subject) es el estándar JWT para user_id
            "email": email
        }
        
        # Crear tokens
        access_token = self.jwt_service.create_access_token(token_data)
        refresh_token = self.jwt_service.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def validate_password_strength(self, password: str) -> tuple[bool, Optional[str]]:
        """
        Valida la fortaleza de una contraseña.
        
        Args:
            password: Contraseña a validar
            
        Returns:
            Tupla (es_válida, mensaje_error)
        """
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe contener al menos una mayúscula"
        
        if not any(c.islower() for c in password):
            return False, "La contraseña debe contener al menos una minúscula"
        
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe contener al menos un número"
        
        return True, None


# Instancias globales
password_service = PasswordService()
jwt_service = JWTService()
auth_service = AuthService()
