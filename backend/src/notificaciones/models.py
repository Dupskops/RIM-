"""
Modelos de base de datos para el módulo de notificaciones.
Alineado con CREATE_TABLES_MVP_V2.2.sql
"""
from sqlalchemy import Integer, String, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey, Time
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, time
from typing import Optional, Dict, Any
import enum

from src.shared.models import BaseModel


class TipoNotificacion(str, enum.Enum):
    """Tipos de notificaciones del sistema (tipo_notificacion ENUM)."""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    SUCCESS = "success"
    ERROR = "error"


class CanalNotificacion(str, enum.Enum):
    """Canales de envío de notificaciones (canal_notificacion ENUM)."""
    IN_APP = "in_app"  # Notificación en la app
    EMAIL = "email"     # Correo electrónico
    PUSH = "push"       # Push notification (móvil)
    SMS = "sms"         # SMS (futuro)


class EstadoNotificacion(str, enum.Enum):
    """Estados de una notificación (estado_notificacion ENUM)."""
    PENDIENTE = "pendiente"
    ENVIADA = "enviada"
    LEIDA = "leida"
    FALLIDA = "fallida"


class ReferenciaNotificacion(str, enum.Enum):
    """Tipos de referencia para notificaciones (referencia_tipo_enum)."""
    FALLA = "falla"
    MANTENIMIENTO = "mantenimiento"
    SENSOR = "sensor"
    PREDICCION = "prediccion"


class Notificacion(BaseModel):
    """
    Modelo de notificación del sistema.
    
    Tabla: notificaciones
    Esquema: CREATE_TABLES_MVP_V2.2.sql
    
    Representa una notificación que puede ser enviada a un usuario
    a través de múltiples canales (in-app, email, push, sms).
    
    Campos según SQL v2.2:
    - usuario_id, titulo, mensaje
    - tipo (tipo_notificacion ENUM)
    - canal (canal_notificacion ENUM)
    - estado (estado_notificacion ENUM)
    - referencia_tipo (referencia_tipo_enum), referencia_id
    - leida, leida_en, intentos_envio
    - created_at, updated_at, deleted_at (heredados de BaseModel)
    """
    __tablename__ = "notificaciones"
    
    # Destinatario
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID del usuario destinatario"
    )
    
    # Contenido
    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Título de la notificación"
    )
    
    mensaje: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Mensaje de la notificación"
    )
    
    tipo: Mapped[str] = mapped_column(
        SQLEnum("info", "warning", "alert", "success", "error", name="tipo_notificacion", native_enum=True),
        nullable=False,
        comment="Tipo: info, warning, alert, success, error"
    )
    
    # Canal y estado
    canal: Mapped[str] = mapped_column(
        SQLEnum("in_app", "email", "push", "sms", name="canal_notificacion", native_enum=True),
        nullable=False,
        comment="Canal: in_app, email, push, sms"
    )
    
    estado: Mapped[str] = mapped_column(
        SQLEnum("pendiente", "enviada", "leida", "fallida", name="estado_notificacion", native_enum=True),
        nullable=False,
        default="pendiente",
        server_default="pendiente",
        comment="Estado: pendiente, enviada, leida, fallida"
    )
    
    # Referencia (opcional - a qué objeto hace referencia)
    referencia_tipo: Mapped[Optional[str]] = mapped_column(
        SQLEnum("falla", "mantenimiento", "sensor", "prediccion", name="referencia_tipo_enum", native_enum=True),
        nullable=True,
        comment="Tipo de referencia: falla, mantenimiento, sensor, prediccion"
    )
    
    referencia_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="ID del objeto referenciado"
    )
    
    # Control de lectura
    leida: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Indica si la notificación fue leída"
    )
    
    leida_en: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fecha y hora de lectura"
    )
    
    # Control de envío (para reintentos)
    intentos_envio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Número de intentos de envío realizados"
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="notificaciones")
    
    def __repr__(self) -> str:
        return f"<Notificacion {self.id}: {self.titulo} [{self.estado.value}]>"
    
    def marcar_como_leida(self) -> None:
        """Marca la notificación como leída."""
        from datetime import timezone
        self.leida = True
        self.leida_en = datetime.now(timezone.utc)
        if self.estado == EstadoNotificacion.ENVIADA:
            self.estado = EstadoNotificacion.LEIDA
    
    def marcar_como_enviada(self) -> None:
        """Marca la notificación como enviada."""
        self.estado = EstadoNotificacion.ENVIADA
        self.intentos_envio += 1
    
    def marcar_como_fallida(self) -> None:
        """Marca la notificación como fallida."""
        self.estado = EstadoNotificacion.FALLIDA
        self.intentos_envio += 1
    
    @property
    def puede_reintentarse(self) -> bool:
        """Verifica si se puede reintentar el envío (máximo 3 intentos)."""
        return (
            self.estado == EstadoNotificacion.FALLIDA and
            self.intentos_envio < 3
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la notificación a diccionario."""
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "tipo": self.tipo,
            "canal": self.canal,
            "estado": self.estado,
            "referencia_tipo": self.referencia_tipo,
            "referencia_id": self.referencia_id,
            "leida": self.leida,
            "leida_en": self.leida_en.isoformat() if self.leida_en else None,
            "intentos_envio": self.intentos_envio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PreferenciaNotificacion(BaseModel):
    """
    Preferencias de notificaciones por usuario.
    
    Tabla: preferencias_notificaciones
    Esquema: CREATE_TABLES_MVP_V2.2.sql
    
    Permite a los usuarios controlar qué notificaciones reciben
    y por qué canales.
    
    Campos según SQL v2.2:
    - usuario_id (UNIQUE)
    - canales_habilitados (JSONB): {"in_app": true, "email": false, "push": false, "sms": false}
    - tipos_habilitados (JSONB): {"fallas": true, "mantenimiento": true, "predicciones": true}
    - no_molestar_inicio (TIME), no_molestar_fin (TIME)
    - configuracion_adicional (JSONB)
    - created_at, updated_at (sin deleted_at según SQL)
    """
    __tablename__ = "preferencias_notificaciones"
    
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID del usuario"
    )
    
    # Canales habilitados (JSONB según SQL v2.2)
    # Default: '{"in_app": true, "email": false, "push": false, "sms": false}'::jsonb
    canales_habilitados: Mapped[Optional[Dict[str, bool]]] = mapped_column(
        JSONB,
        nullable=True,
        default={"in_app": True, "email": False, "push": False, "sms": False},
        server_default='{"in_app": true, "email": false, "push": false, "sms": false}',
        comment="Canales habilitados por usuario"
    )
    
    # Tipos de notificaciones habilitadas (JSONB según SQL v2.2)
    # Default: '{"fallas": true, "mantenimiento": true, "predicciones": true}'::jsonb
    tipos_habilitados: Mapped[Optional[Dict[str, bool]]] = mapped_column(
        JSONB,
        nullable=True,
        default={"fallas": True, "mantenimiento": True, "predicciones": True},
        server_default='{"fallas": true, "mantenimiento": true, "predicciones": true}',
        comment="Tipos de notificaciones habilitadas"
    )
    
    # Horarios "No molestar" (TIME según SQL v2.2)
    no_molestar_inicio: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Hora inicio período No molestar (ej: 22:00)"
    )
    
    no_molestar_fin: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
        comment="Hora fin período No molestar (ej: 08:00)"
    )
    # Configuración adicional (JSONB)
    configuracion_adicional: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Configuración extra del usuario"
    )

    # Excluir deleted_at ya que no existe en la tabla
    deleted_at = None
    
    def __repr__(self) -> str:
        return f"<PreferenciaNotificacion usuario_id={self.usuario_id}>"
    
    def canal_habilitado(self, canal: CanalNotificacion) -> bool:
        """Verifica si un canal está habilitado."""
        
        canal_key = canal  # "in_app", "email", "push", "sms"
        return self.canales_habilitados.get(canal_key, False)
    
    def tipo_notificacion_habilitado(self, tipo: str) -> bool:
        """
        Verifica si un tipo de notificación está habilitado.
        
        Args:
            tipo: "fallas", "mantenimiento", "predicciones", "sensores", etc.
        
        Returns:
            True si el tipo está habilitado, False en caso contrario
        """
        if not self.tipos_habilitados:
            return True  # Por defecto permitir si no hay configuración
        
        return self.tipos_habilitados.get(tipo, True)
    
    def esta_en_horario_no_molestar(self) -> bool:
        """
        Verifica si actualmente está en horario "No molestar".
        
        Returns:
            True si está en horario "No molestar", False en caso contrario
        """
        if not self.no_molestar_inicio or not self.no_molestar_fin:
            return False
        
        from datetime import timezone
        hora_actual = datetime.now(timezone.utc).time()
        
        # Caso 1: Rango dentro del mismo día (ej: 22:00 - 23:59)
        if self.no_molestar_inicio <= self.no_molestar_fin:
            return self.no_molestar_inicio <= hora_actual <= self.no_molestar_fin
        
        # Caso 2: Rango que cruza medianoche (ej: 22:00 - 08:00)
        return hora_actual >= self.no_molestar_inicio or hora_actual <= self.no_molestar_fin
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las preferencias a diccionario."""
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "canales_habilitados": self.canales_habilitados,
            "tipos_habilitados": self.tipos_habilitados,
            "no_molestar_inicio": self.no_molestar_inicio.isoformat() if self.no_molestar_inicio else None,
            "no_molestar_fin": self.no_molestar_fin.isoformat() if self.no_molestar_fin else None,
            "configuracion_adicional": self.configuracion_adicional,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
