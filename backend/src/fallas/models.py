"""
Modelos de base de datos para el módulo de fallas.
Representa fallas detectadas en las motos y su tracking.

MVP v2.3 - Alineado con CREATE_TABLES_MVP_V2.2.sql
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..shared.models import BaseModel
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID


# ============================================
# ENUMS - Deben coincidir con PostgreSQL
# ============================================

class SeveridadFalla(str, enum.Enum):
    """Severidad de la falla (severidad_falla ENUM)"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoFalla(str, enum.Enum):
    """Estado de la falla (estado_falla ENUM)"""
    DETECTADA = "detectada"
    EN_REPARACION = "en_reparacion"
    RESUELTA = "resuelta"


class OrigenDeteccion(str, enum.Enum):
    """Origen de detección de la falla (origen_deteccion ENUM)"""
    SENSOR = "sensor"
    ML = "ml"
    MANUAL = "manual"


class Falla(BaseModel):
    """
    Modelo de falla detectada en una moto.
    
    Representa una anomalía o problema identificado por:
    - Sensores IoT (lecturas fuera de rango)
    - ML/IA (detección predictiva)
    - Usuario (reporte manual)
    
    Schema: CREATE_TABLES_MVP_V2.2.sql línea 468
    """
    
    __tablename__ = "fallas"
    
    # Relaciones (Foreign Keys)
    moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("motos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    sensor_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sensores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Sensor que detectó la falla (si aplica)"
    )
    
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False,
        index=True,
        comment="Componente afectado"
    )
    
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        comment="Usuario que reportó la falla (si es manual)"
    )
    
    # Información de la falla
    codigo: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Código único (FL-YYYYMMDD-NNN)"
    )

    tipo: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Tipo de falla (ej: sobrecalentamiento, bateria_baja)"
    )
    
    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Título descriptivo de la falla"
    )
    
    descripcion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción detallada de la falla"
    )
    
    # ENUMs nativos de PostgreSQL
    severidad: Mapped[SeveridadFalla] = mapped_column(
        SQLEnum(SeveridadFalla, native_enum=True, name="severidad_falla", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
        comment="Severidad: baja, media, alta, critica"
    )
    
    estado: Mapped[EstadoFalla] = mapped_column(
        SQLEnum(EstadoFalla, native_enum=True, name="estado_falla", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=EstadoFalla.DETECTADA,
        index=True,
        comment="Estado: detectada, en_reparacion, resuelta"
    )
    
    origen_deteccion: Mapped[OrigenDeteccion] = mapped_column(
        SQLEnum(OrigenDeteccion, native_enum=True, name="origen_deteccion", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        comment="Origen: sensor, ml, manual"
    )
    
    # Datos técnicos del sensor
    valor_actual: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Valor del sensor al momento de detectar la falla"
    )
    
    valor_esperado: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Valor esperado del sensor"
    )
    
    # Flags de acción
    requiere_atencion_inmediata: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Si requiere atención urgente"
    )
    
    puede_conducir: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Si es seguro conducir con esta falla"
    )
    
    solucion_sugerida: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Solución o pasos sugeridos para resolver"
    )
    
    # Fechas
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Cuándo se detectó la falla"
    )
    
    fecha_resolucion: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cuándo se resolvió la falla"
    )
    
    # Relaciones SQLAlchemy
    moto = relationship("Moto", back_populates="fallas")
    componente = relationship("Componente", back_populates="fallas")
    sensor = relationship("Sensor", back_populates="fallas")
    usuario = relationship("Usuario", back_populates="fallas_reportadas")
    mantenimientos = relationship("Mantenimiento", back_populates="falla_relacionada")
    
    def __repr__(self) -> str:
        return (
            f"<Falla {self.codigo} | "
            f"Moto: {self.moto_id} | "
            f"Tipo: {self.tipo} | "
            f"Severidad: {self.severidad.value if isinstance(self.severidad, SeveridadFalla) else self.severidad}>"
        )
    
    @property
    def esta_resuelta(self) -> bool:
        """Verifica si la falla está resuelta."""
        return (self.estado == EstadoFalla.RESUELTA if isinstance(self.estado, EstadoFalla) 
                else self.estado == EstadoFalla.RESUELTA.value)
    
    @property
    def dias_sin_resolver(self) -> int:
        """Calcula días desde la detección sin resolver."""
        if self.esta_resuelta:
            return 0
        delta = datetime.now(timezone.utc) - self.fecha_deteccion
        return delta.days
    
    @property
    def es_critica(self) -> bool:
        """Verifica si es una falla crítica."""
        return (self.severidad == SeveridadFalla.CRITICA if isinstance(self.severidad, SeveridadFalla)
                else self.severidad == SeveridadFalla.CRITICA.value)
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario, serializando ENUMs correctamente."""
        return {
            "id": self.id,
            "moto_id": self.moto_id,
            "sensor_id": str(self.sensor_id) if self.sensor_id else None,
            "componente_id": self.componente_id,
            "usuario_id": self.usuario_id,
            "codigo": self.codigo,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "severidad": self.severidad.value if isinstance(self.severidad, SeveridadFalla) else self.severidad,
            "estado": self.estado.value if isinstance(self.estado, EstadoFalla) else self.estado,
            "origen_deteccion": self.origen_deteccion.value if isinstance(self.origen_deteccion, OrigenDeteccion) else self.origen_deteccion,
            "valor_actual": float(self.valor_actual) if self.valor_actual else None,
            "valor_esperado": float(self.valor_esperado) if self.valor_esperado else None,
            "requiere_atencion_inmediata": self.requiere_atencion_inmediata,
            "puede_conducir": self.puede_conducir,
            "solucion_sugerida": self.solucion_sugerida,
            "fecha_deteccion": self.fecha_deteccion.isoformat() if self.fecha_deteccion else None,
            "fecha_resolucion": self.fecha_resolucion.isoformat() if self.fecha_resolucion else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
