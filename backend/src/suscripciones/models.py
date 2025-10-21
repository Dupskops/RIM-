"""
Modelos de base de datos para suscripciones.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Boolean, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from src.shared.models import BaseModel


class PlanType(str, Enum):
    """Tipos de plan de suscripción."""
    FREEMIUM = "freemium"
    PREMIUM = "premium"


class SuscripcionStatus(str, Enum):
    """Estados de suscripción."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class Suscripcion(BaseModel):
    """Modelo de suscripción de usuario."""
    
    __tablename__ = "suscripciones"
    
    # Campos principales
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        index=True,
        nullable=False,
        comment="ID del usuario"
    )
    
    # Plan
    plan: Mapped[str] = mapped_column(
        SQLEnum(PlanType, native_enum=False),
        default=PlanType.FREEMIUM,
        nullable=False,
        index=True,
        comment="Tipo de plan"
    )
    
    # Estado
    status: Mapped[str] = mapped_column(
        SQLEnum(SuscripcionStatus, native_enum=False),
        default=SuscripcionStatus.ACTIVE,
        nullable=False,
        index=True,
        comment="Estado de la suscripción"
    )
    
    # Fechas
    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha de inicio"
    )
    
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Fecha de fin (null = sin límite para freemium)"
    )
    
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Fecha de cancelación"
    )
    
    # Pago
    precio: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Precio pagado (null para freemium)"
    )
    
    metodo_pago: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Método de pago utilizado"
    )
    
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="ID de transacción del pago"
    )
    
    # Renovación
    auto_renovacion: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si se renueva automáticamente"
    )
    
    # Notas
    notas: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas adicionales"
    )
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="suscripcion")
    
    # BaseModel ya proporciona: id, created_at, updated_at, deleted_at
    
    # Propiedades computadas
    @property
    def is_active(self) -> bool:
        """Verifica si la suscripción está activa."""
        if self.status != SuscripcionStatus.ACTIVE:
            return False
        
        if self.end_date and self.end_date < datetime.utcnow():
            return False
        
        return True
    
    @property
    def is_premium(self) -> bool:
        """Verifica si es plan premium."""
        return self.plan == PlanType.PREMIUM
    
    @property
    def is_freemium(self) -> bool:
        """Verifica si es plan freemium."""
        return self.plan == PlanType.FREEMIUM
    
    @property
    def dias_restantes(self) -> Optional[int]:
        """Calcula días restantes de la suscripción."""
        if not self.end_date:
            return None
        
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def __repr__(self) -> str:
        return f"<Suscripcion {self.id} - Usuario {self.usuario_id} - {self.plan}>"
