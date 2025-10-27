"""
Modelos de motos.
Define la entidad Moto y MotoComponente para el sistema.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import enum

from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP, text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from src.shared.models import BaseModel, Base


class ComponentState(str, enum.Enum):
    """Estado agregado del componente físico (basado en sensores)."""
    OK = "ok"
    WARNING = "warning"       # Atención requerida
    MODERATE = "moderate"     # Degradación moderada
    CRITICAL = "critical"     # Requiere intervención urgente
    UNKNOWN = "unknown"


class Moto(BaseModel):
    """
    Modelo de moto KTM.
    
    Representa una motocicleta registrada en el sistema.
    Cada moto pertenece a un usuario y tiene características específicas.
    """
    
    __tablename__ = "motos"
    
    # Información del propietario
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID del usuario propietario"
    )
    
    # Información de la moto
    marca = Column(
        String(50),
        nullable=False,
        default="KTM",
        comment="Marca de la moto (siempre KTM)"
    )
    modelo = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Modelo de la moto (ej: Duke 390, Adventure 790)"
    )
    año = Column(
        Integer,
        nullable=False,
        index=True,
        comment="Año de fabricación"
    )
    vin = Column(
        String(17),
        unique=True,
        nullable=False,
        index=True,
        comment="VIN (Vehicle Identification Number) - 17 caracteres"
    )
    placa = Column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
        comment="Placa de matrícula"
    )
    color = Column(
        String(50),
        nullable=True,
        comment="Color de la moto"
    )
    kilometraje = Column(
        Integer,
        nullable=True,
        default=0,
        comment="Kilometraje actual"
    )
    
    # Información adicional
    observaciones = Column(
        Text,
        nullable=True,
        comment="Observaciones o notas sobre la moto"
    )
    
    # Relaciones
    usuario = relationship(
        "Usuario",
        back_populates="motos",
        lazy="selectin"
    )
    
    conversaciones = relationship(
        "Conversacion",
        back_populates="moto",
        lazy="selectin"
    )
    
    sensores = relationship(
        "Sensor",
        back_populates="moto",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    fallas = relationship(
        "Falla",
        back_populates="moto",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    mantenimientos = relationship(
        "Mantenimiento",
        back_populates="moto",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    componentes = relationship(
        "MotoComponente",
        back_populates="moto",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Moto {self.marca} {self.modelo} ({self.año}) - VIN: {self.vin}>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo de la moto."""
        return f"{self.marca} {self.modelo} ({self.año})"
    
    @property
    def es_ktm(self) -> bool:
        """Verifica si la moto es KTM."""
        return self.marca.upper() == "KTM"


class MotoComponente(Base):
    """
    Componente físico de una moto con estado agregado.
    
    El component_state se calcula mediante agregación de sensores asociados.
    NO se modifica por predicciones ML, solo por lecturas reales.
    
    Ejemplos de componentes:
    - engine (motor)
    - brakes (frenos)
    - suspension (suspensión)
    - transmission (transmisión)
    - electrical (sistema eléctrico)
    """
    
    __tablename__ = "moto_componentes"
    
    # Redefinir id como UUID para este modelo
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    moto_id = Column(
        Integer,
        ForeignKey("motos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID de la moto a la que pertenece"
    )
    
    tipo = Column(
        String(64),
        nullable=False,
        index=True,
        comment="Tipo de componente (engine, brakes, etc)"
    )
    
    nombre = Column(
        String(128),
        nullable=True,
        comment="Nombre descriptivo del componente"
    )
    
    component_state: Mapped[ComponentState] = mapped_column(
        SQLEnum(ComponentState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=ComponentState.UNKNOWN.value,
        comment="Estado agregado del componente"
    )
    
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Última actualización del estado"
    )
    
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Metadata de agregación (sensor_states, scores, etc)"
    )
    
    # Relaciones
    moto = relationship(
        "Moto",
        back_populates="componentes"
    )
    
    sensores = relationship(
        "Sensor",
        back_populates="componente",
        foreign_keys="[Sensor.componente_id]"
    )
    
    @property
    def is_healthy(self) -> bool:
        """Componente en estado saludable."""
        return self.component_state == ComponentState.OK
    
    @property
    def needs_attention(self) -> bool:
        """Componente requiere atención."""
        return self.component_state in [ComponentState.WARNING, ComponentState.MODERATE]
    
    @property
    def is_critical(self) -> bool:
        """Componente en estado crítico."""
        return self.component_state == ComponentState.CRITICAL
    
    def __repr__(self):
        return f"<MotoComponente(id={self.id}, tipo='{self.tipo}', state={self.component_state.value})>"

