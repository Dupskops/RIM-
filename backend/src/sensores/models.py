"""
Modelos de base de datos para sensores IoT.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from ..shared.models import BaseModel
from ..shared.constants import TipoSensor


class EstadoSensor(str, Enum):
    """Estados de un sensor."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class Sensor(BaseModel):
    """Modelo de sensor IoT instalado en una moto."""
    
    __tablename__ = "sensores"
    
    # Relación con moto
    moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("motos.id"),
        nullable=False,
        index=True,
        comment="ID de la moto"
    )
    
    # Tipo de sensor
    tipo: Mapped[str] = mapped_column(
        SQLEnum(TipoSensor, native_enum=False),
        nullable=False,
        index=True,
        comment="Tipo de sensor"
    )
    
    # Identificación
    codigo: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Código único del sensor"
    )
    
    nombre: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nombre descriptivo del sensor"
    )
    
    # Ubicación física
    ubicacion: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Ubicación física en la moto"
    )
    
    # Estado
    estado: Mapped[str] = mapped_column(
        SQLEnum(EstadoSensor, native_enum=False),
        default=EstadoSensor.ACTIVE,
        nullable=False,
        index=True,
        comment="Estado del sensor"
    )
    
    # Configuración
    frecuencia_lectura: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="Frecuencia de lectura en segundos"
    )
    
    umbral_min: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Umbral mínimo para alertas"
    )
    
    umbral_max: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Umbral máximo para alertas"
    )
    
    # Metadata del dispositivo
    fabricante: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Fabricante del sensor"
    )
    
    modelo: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Modelo del sensor"
    )
    
    version_firmware: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Versión del firmware"
    )
    
    # Timestamps adicionales
    ultima_lectura: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Timestamp de la última lectura"
    )
    
    ultima_calibracion: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Timestamp de la última calibración"
    )
    
    # Notas
    notas: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas adicionales"
    )
    
    # Relaciones
    moto = relationship("Moto", back_populates="sensores")
    lecturas = relationship("LecturaSensor", back_populates="sensor", cascade="all, delete-orphan")
    fallas = relationship("Falla", back_populates="sensor")
    
    def __repr__(self) -> str:
        return f"<Sensor {self.codigo} - {self.tipo}>"
    
    @property
    def is_active(self) -> bool:
        """Verifica si el sensor está activo."""
        return self.estado == EstadoSensor.ACTIVE
    
    @property
    def needs_maintenance(self) -> bool:
        """Verifica si el sensor necesita mantenimiento."""
        return self.estado == EstadoSensor.MAINTENANCE
    
    @property
    def has_error(self) -> bool:
        """Verifica si el sensor tiene error."""
        return self.estado == EstadoSensor.ERROR


class LecturaSensor(BaseModel):
    """Modelo de lectura de sensor."""
    
    __tablename__ = "lecturas_sensores"
    
    # Relación con sensor
    sensor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sensores.id"),
        nullable=False,
        index=True,
        comment="ID del sensor"
    )
    
    # Valor medido
    valor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Valor de la lectura"
    )
    
    # Unidad de medida
    unidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unidad de medida"
    )
    
    # Timestamp de la lectura (del dispositivo IoT)
    timestamp_lectura: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        comment="Timestamp de la lectura del dispositivo"
    )
    
    # Indicadores de calidad
    fuera_rango: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si el valor está fuera del rango normal"
    )
    
    alerta_generada: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si se generó una alerta"
    )
    
    # Metadata adicional (JSON)
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Metadata adicional en formato JSON"
    )
    
    # Relaciones
    sensor = relationship("Sensor", back_populates="lecturas")
    
    def __repr__(self) -> str:
        return f"<LecturaSensor {self.sensor_id}: {self.valor} {self.unidad}>"
    
    @property
    def is_anomaly(self) -> bool:
        """Verifica si la lectura es una anomalía."""
        return self.fuera_rango or self.alerta_generada
