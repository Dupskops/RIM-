"""
Modelos de motos.
Define la entidad Moto para el sistema.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.shared.models import BaseModel


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
