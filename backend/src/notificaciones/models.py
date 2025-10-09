"""
Modelos de base de datos para el módulo de notificaciones.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from src.shared.models import BaseModel


class TipoNotificacion(str, enum.Enum):
    """Tipos de notificaciones del sistema."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    SUCCESS = "success"
    ERROR = "error"


class CanalNotificacion(str, enum.Enum):
    """Canales de envío de notificaciones."""
    IN_APP = "in_app"  # Notificación en la app
    EMAIL = "email"     # Correo electrónico
    PUSH = "push"       # Push notification (móvil)
    SMS = "sms"         # SMS (futuro)


class EstadoNotificacion(str, enum.Enum):
    """Estados de una notificación."""
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    LEIDA = "leida"
    FALLIDA = "fallida"


class Notificacion(BaseModel):
    """
    Modelo de notificación del sistema.
    
    Representa una notificación que puede ser enviada a un usuario
    a través de múltiples canales (in-app, email, push, sms).
    """
    __tablename__ = "notificaciones"
    
    # Destinatario
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    
    # Contenido
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(SQLEnum(TipoNotificacion), nullable=False, default=TipoNotificacion.INFO)
    
    # Canal y estado
    canal = Column(SQLEnum(CanalNotificacion), nullable=False, default=CanalNotificacion.IN_APP)
    estado = Column(SQLEnum(EstadoNotificacion), nullable=False, default=EstadoNotificacion.PENDIENTE)
    
    # Metadata
    datos_adicionales = Column(JSONB, nullable=True)  # JSON con datos extra
    
    # Acción (opcional)
    accion_url = Column(String(500), nullable=True)  # URL a la que redirigir al hacer click
    accion_tipo = Column(String(50), nullable=True)  # Tipo de acción: "navigate", "external", etc.
    
    # Referencia (opcional)
    referencia_tipo = Column(String(50), nullable=True)  # "falla", "mantenimiento", "sensor", etc.
    referencia_id = Column(Integer, nullable=True)  # ID del objeto referenciado
    
    # Control
    leida = Column(Boolean, default=False, nullable=False)
    leida_en = Column(DateTime, nullable=True)
    
    enviada = Column(Boolean, default=False, nullable=False)
    enviada_en = Column(DateTime, nullable=True)
    
    # Reintento (para notificaciones fallidas)
    intentos_envio = Column(Integer, default=0, nullable=False)
    ultimo_error = Column(Text, nullable=True)
    
    # Expiración (opcional)
    expira_en = Column(DateTime, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="notificaciones")
    
    def __repr__(self):
        return f"<Notificacion {self.id}: {self.titulo} - {self.estado}>"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída."""
        self.leida = True
        self.leida_en = datetime.utcnow()
        if self.estado == EstadoNotificacion.ENVIADA:
            self.estado = EstadoNotificacion.LEIDA
    
    def marcar_como_enviada(self):
        """Marca la notificación como enviada."""
        self.enviada = True
        self.enviada_en = datetime.utcnow()
        self.estado = EstadoNotificacion.ENVIADA
    
    def marcar_como_fallida(self, error: str):
        """Marca la notificación como fallida."""
        self.estado = EstadoNotificacion.FALLIDA
        self.ultimo_error = error
        self.intentos_envio += 1
    
    @property
    def esta_expirada(self) -> bool:
        """Verifica si la notificación está expirada."""
        if self.expira_en is None:
            return False
        return datetime.utcnow() > self.expira_en
    
    @property
    def puede_reintentarse(self) -> bool:
        """Verifica si se puede reintentar el envío."""
        return (
            self.estado == EstadoNotificacion.FALLIDA and
            self.intentos_envio < 3 and
            not self.esta_expirada
        )


class PreferenciaNotificacion(BaseModel):
    """
    Preferencias de notificaciones por usuario.
    
    Permite a los usuarios controlar qué notificaciones reciben
    y por qué canales.
    """
    __tablename__ = "preferencias_notificaciones"
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, unique=True, index=True)
    
    # Canales habilitados
    in_app_habilitado = Column(Boolean, default=True, nullable=False)
    email_habilitado = Column(Boolean, default=True, nullable=False)
    push_habilitado = Column(Boolean, default=False, nullable=False)
    sms_habilitado = Column(Boolean, default=False, nullable=False)
    
    # Tipos de notificaciones habilitadas
    notif_fallas_habilitado = Column(Boolean, default=True, nullable=False)
    notif_mantenimiento_habilitado = Column(Boolean, default=True, nullable=False)
    notif_sensores_habilitado = Column(Boolean, default=True, nullable=False)
    notif_sistema_habilitado = Column(Boolean, default=True, nullable=False)
    notif_marketing_habilitado = Column(Boolean, default=False, nullable=False)
    
    # Horarios (opcional - para no molestar)
    no_molestar_inicio = Column(String(5), nullable=True)  # "22:00"
    no_molestar_fin = Column(String(5), nullable=True)     # "08:00"
    
    # Configuración adicional
    configuracion_adicional = Column(JSONB, nullable=True)
    
    def __repr__(self):
        return f"<PreferenciaNotificacion usuario_id={self.usuario_id}>"
    
    def canal_habilitado(self, canal: CanalNotificacion) -> bool:
        """Verifica si un canal está habilitado."""
        if canal == CanalNotificacion.IN_APP:
            return self.in_app_habilitado
        elif canal == CanalNotificacion.EMAIL:
            return self.email_habilitado
        elif canal == CanalNotificacion.PUSH:
            return self.push_habilitado
        elif canal == CanalNotificacion.SMS:
            return self.sms_habilitado
        return False
    
    def tipo_notificacion_habilitado(self, tipo_referencia: str) -> bool:
        """Verifica si un tipo de notificación está habilitado."""
        if tipo_referencia == "falla":
            return self.notif_fallas_habilitado
        elif tipo_referencia == "mantenimiento":
            return self.notif_mantenimiento_habilitado
        elif tipo_referencia == "sensor":
            return self.notif_sensores_habilitado
        elif tipo_referencia == "sistema":
            return self.notif_sistema_habilitado
        elif tipo_referencia == "marketing":
            return self.notif_marketing_habilitado
        return True  # Por defecto, permitir
