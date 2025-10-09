"""
Modelos de base de datos para el módulo de chatbot.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models import BaseModel


class Conversacion(BaseModel):
    """
    Modelo de conversación del chatbot.
    
    Almacena el historial completo de conversaciones entre usuario y chatbot.
    """
    __tablename__ = "conversaciones"

    # Identificación (id ya está en BaseModel)
    conversation_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    # Usuario
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    
    # Contexto
    moto_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("motos.id"), nullable=True, index=True)
    
    # Metadata
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    nivel_acceso: Mapped[str] = mapped_column(String(20), nullable=False, default="freemium")  # freemium/premium
    
    # Estado
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    total_mensajes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Fechas
    ultima_actividad: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="conversaciones")
    moto = relationship("Moto", back_populates="conversaciones")
    mensajes = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Conversacion(id={self.id}, conversation_id='{self.conversation_id}', "
            f"usuario_id={self.usuario_id}, total_mensajes={self.total_mensajes})>"
        )


class Mensaje(BaseModel):
    """
    Modelo de mensaje individual en una conversación.
    
    Almacena cada mensaje enviado por el usuario o generado por el chatbot.
    """
    __tablename__ = "mensajes"

    # Identificación (id ya está en BaseModel)
    
    # Relación con conversación
    conversacion_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversaciones.id"), nullable=False, index=True)
    
    # Contenido
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" o "assistant"
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata del mensaje
    tokens_usados: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tiempo_respuesta_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    modelo_usado: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Contexto usado (para mensajes del asistente)
    contexto_usado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON con datos de contexto
    tipo_prompt: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # diagnostic/maintenance/explanation
    
    # Confianza y calidad
    confianza: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Feedback del usuario
    util: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relaciones
    conversacion = relationship("Conversacion", back_populates="mensajes")

    def __repr__(self) -> str:
        contenido_preview = self.contenido[:50] + "..." if len(self.contenido) > 50 else self.contenido
        return (
            f"<Mensaje(id={self.id}, role='{self.role}', "
            f"contenido='{contenido_preview}')>"
        )
