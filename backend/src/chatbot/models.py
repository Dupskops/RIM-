"""
Modelos de base de datos para el módulo de chatbot.

Alineado con MVP v2.3 - Sistema de límites Freemium.
Las conversaciones del chatbot están limitadas a 5/mes para usuarios Free.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, ForeignKey, Boolean, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from src.shared.models import BaseModel


class RoleMensaje(str, enum.Enum):
    """Rol del mensaje en la conversación."""
    user = "user"
    assistant = "assistant"


class TipoPrompt(str, enum.Enum):
    """
    Tipo de prompt usado para generar la respuesta.
    
    MVP v2.3 - Tipos expandidos:
    - diagnostic: Diagnóstico de problemas mecánicos
    - maintenance: Recomendaciones de mantenimiento
    - explanation: Explicaciones educativas sobre motocicletas
    - ml_analysis: Análisis ML completo de componentes (Flujo #7)
    - trip_analysis: Análisis de viajes y patrones de conducción (Flujo #8)
    - sensor_reading: Interpretación de lecturas de sensores en tiempo real (Flujo #3)
    - freemium: Comparativas de planes y funcionalidades (Flujo #9)
    - general: Conversación general
    """
    diagnostic = "diagnostic"
    maintenance = "maintenance"
    explanation = "explanation"
    ml_analysis = "ml_analysis"
    trip_analysis = "trip_analysis"
    sensor_reading = "sensor_reading"
    freemium = "freemium"
    general = "general"


class Conversacion(BaseModel):
    """
    Modelo de conversación del chatbot.
    
    Almacena el historial completo de conversaciones entre usuario y chatbot.
    Límite Free: 5 conversaciones por mes.
    Plan Pro: conversaciones ilimitadas.
    
    Alineado con tabla 'conversaciones' del DDL MVP v2.3.
    """
    __tablename__ = "conversaciones"
    
    __table_args__ = (
        CheckConstraint('total_mensajes >= 0', name='chk_total_mensajes_no_negativo'),
    )

    # Identificación única de la conversación
    conversation_id: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="ID único de la conversación (ej: conv_20251110_abc123)"
    )
    
    # Relaciones obligatorias
    usuario_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("usuarios.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="Usuario propietario de la conversación"
    )
    
    moto_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("motos.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="Moto sobre la que trata la conversación"
    )
    
    # Metadata
    titulo: Mapped[Optional[str]] = mapped_column(
        String(200), 
        nullable=True,
        comment="Título generado automáticamente o personalizado"
    )
    
    # Estado de la conversación
    activa: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        index=True,
        comment="True si la conversación está activa (no archivada)"
    )
    
    total_mensajes: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="Contador de mensajes en la conversación"
    )
    
    # Timestamp de última interacción
    ultima_actividad: Mapped[datetime] = mapped_column(
        "ultima_actividad",
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Timestamp de la última actividad en la conversación"
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="conversaciones")
    moto = relationship("Moto", back_populates="conversaciones")
    mensajes = relationship(
        "Mensaje", 
        back_populates="conversacion", 
        cascade="all, delete-orphan",
        order_by="Mensaje.created_at"
    )

    def __repr__(self) -> str:
        return (
            f"<Conversacion(id={self.id}, conversation_id='{self.conversation_id}', "
            f"usuario_id={self.usuario_id}, moto_id={self.moto_id}, "
            f"total_mensajes={self.total_mensajes}, activa={self.activa})>"
        )


class Mensaje(BaseModel):
    """
    Modelo de mensaje individual en una conversación.
    
    Almacena cada mensaje enviado por el usuario o generado por el chatbot.
    Los mensajes se ordenan cronológicamente y forman el historial de la conversación.
    
    Alineado con tabla 'mensajes' del DDL MVP v2.3.
    """
    __tablename__ = "mensajes"

    # Relación con conversación (obligatoria)
    conversacion_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("conversaciones.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="ID de la conversación a la que pertenece el mensaje"
    )
    
    # Rol del mensaje
    role: Mapped[RoleMensaje] = mapped_column(
        SQLEnum(RoleMensaje, native_enum=True, name="role_mensaje"),
        nullable=False,
        index=True,
        comment="Rol del mensaje: user (usuario) o assistant (chatbot)"
    )
    
    # Contenido del mensaje
    contenido: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        comment="Contenido textual del mensaje"
    )
    
    # Tipo de prompt (solo para mensajes del assistant)
    tipo_prompt: Mapped[TipoPrompt] = mapped_column(
        SQLEnum(TipoPrompt, native_enum=True, name="tipo_prompt"),
        default=TipoPrompt.general,
        nullable=True,
        comment="Tipo de prompt usado: diagnostic, maintenance, explanation, general"
    )
    
    # Métricas de LLM (MVP v2.3 - solo para mensajes del assistant)
    tokens_usados: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="Tokens generados por el LLM para este mensaje"
    )
    
    tiempo_respuesta_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="Tiempo de respuesta del LLM en milisegundos"
    )
    
    modelo_usado: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
        nullable=True,
        comment="Modelo de LLM usado (ej: llama3, mistral)"
    )
    
    # Relaciones
    conversacion = relationship("Conversacion", back_populates="mensajes")

    def __repr__(self) -> str:
        contenido_preview = self.contenido[:50] + "..." if len(self.contenido) > 50 else self.contenido
        return (
            f"<Mensaje(id={self.id}, conversacion_id={self.conversacion_id}, "
            f"role={self.role.value}, tipo_prompt={self.tipo_prompt.value if self.tipo_prompt else 'None'}, "
            f"contenido='{contenido_preview}')>"
        )
    
    @property
    def es_usuario(self) -> bool:
        """Retorna True si el mensaje fue enviado por el usuario."""
        return self.role == RoleMensaje.user
    
    @property
    def es_asistente(self) -> bool:
        """Retorna True si el mensaje fue generado por el asistente."""
        return self.role == RoleMensaje.assistant
