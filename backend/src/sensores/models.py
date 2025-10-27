"""
Modelos de dominio para el módulo de sensores.

Jerarquía:
- SensorTemplate: Plantillas de sensores por modelo de moto
- Sensor: Instancias de sensores con estado de salud (sensor_state)
- Lectura: Telemetría raw de sensores

Nota: MotoComponente está en motos/models.py

Estados:
- sensor_state: ok, degraded, faulty, offline, unknown (salud del sensor)
- component_state: ok, warning, moderate, critical, unknown (en motos/models.py)

PKs: UUID para tablas de sensores
FKs: int para referencias a otros módulos (motos, etc.)
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import String, TIMESTAMP, Integer, text, Enum as SQLEnum, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from ..shared.models import Base


# ============================================
# ENUMS
# ============================================

class SensorState(str, enum.Enum):
    """Estado de salud del sensor (hardware/conectividad)."""
    OK = "ok"
    DEGRADED = "degraded"  # Intermitente, con errores
    FAULTY = "faulty"       # Mal funcionamiento confirmado
    OFFLINE = "offline"     # Sin conexión
    UNKNOWN = "unknown"     # Estado indeterminado


# ============================================
# MODELS
# ============================================

class SensorTemplate(Base):
    """
    Plantilla de sensores por modelo de moto.
    
    Define qué sensores deben aprovisionarse automáticamente
    al registrar una moto de un modelo específico.
    
    Ejemplo definition JSONB:
    {
        "sensor_type": "temperature",
        "unit": "celsius",
        "default_thresholds": {"min": 0, "max": 100},
        "frequency_ms": 1000,
        "component_type": "engine"
    }
    """
    __tablename__ = "sensor_templates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    modelo: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()")
    )

    def __repr__(self):
        return f"<SensorTemplate(id={self.id}, modelo='{self.modelo}', name='{self.name}')>"


class Sensor(Base):
    """
    Sensor instanciado en una moto.
    
    Cada sensor monitorea un aspecto específico y puede estar asociado
    a un componente físico. El sensor_state refleja la salud del sensor mismo.
    
    Ejemplo config JSONB:
    {
        "thresholds": {"min": 10, "max": 90},
        "calibration_offset": 0.5,
        "enabled": true
    }
    
    Ejemplo last_value JSONB:
    {
        "value": 75.3,
        "unit": "celsius",
        "quality": 0.98
    }
    """
    __tablename__ = "sensores"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("motos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sensor_templates.id"),
        nullable=True
    )
    nombre: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tipo: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    componente_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("moto_componentes.id"),
        nullable=True,
        index=True
    )
    
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )
    sensor_state: Mapped[SensorState] = mapped_column(
        SQLEnum(SensorState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        server_default=SensorState.UNKNOWN.value
    )
    last_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()")
    )

    # Relaciones
    moto: Mapped["Moto"] = relationship("Moto", back_populates="sensores")
    template: Mapped[Optional["SensorTemplate"]] = relationship("SensorTemplate")
    componente: Mapped[Optional["MotoComponente"]] = relationship("MotoComponente", back_populates="sensores")
    lecturas: Mapped[list["Lectura"]] = relationship("Lectura", back_populates="sensor", cascade="all, delete-orphan")
    # Relación con fallas detectadas por este sensor (si aplica)
    fallas: Mapped[list["Falla"]] = relationship(
        "Falla", back_populates="sensor", cascade="all, delete-orphan"
    )

    @property
    def is_healthy(self) -> bool:
        """Sensor en estado saludable."""
        return self.sensor_state == SensorState.OK

    @property
    def needs_attention(self) -> bool:
        """Sensor requiere atención."""
        return self.sensor_state in [SensorState.DEGRADED, SensorState.FAULTY, SensorState.OFFLINE]

    def __repr__(self):
        return f"<Sensor(id={self.id}, tipo='{self.tipo}', state={self.sensor_state.value})>"


class Lectura(Base):
    """
    Lectura de telemetría de un sensor.
    
    Esquema simple para MVP. En producción considerar TimescaleDB/particionado.
    
    Ejemplo valor JSONB:
    {
        "value": 75.3,
        "unit": "celsius",
        "raw": 753
    }
    
    Ejemplo metadata JSONB:
    {
        "quality": 0.98,
        "anomaly_score": 0.05,
        "source": "websocket"
    }
    """
    __tablename__ = "lecturas"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("motos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sensor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sensores.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    component_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("moto_componentes.id"),
        nullable=True
    )
    
    ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True
    )
    valor: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)  # Renombrado de metadata
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    # Relaciones
    moto: Mapped["Moto"] = relationship("Moto")
    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="lecturas")
    componente: Mapped[Optional["MotoComponente"]] = relationship("MotoComponente")

    def __repr__(self):
        val = self.valor.get("value", "?") if self.valor else "?"
        return f"<Lectura(id={self.id}, sensor_id={self.sensor_id}, valor={val}, ts={self.ts})>"
