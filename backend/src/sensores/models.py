"""
Modelos de dominio para el módulo de sensores.

Arquitectura v2.3 MVP:
- SensorTemplate: Plantillas de sensores por modelo de moto (ej: temperatura_motor para KTM 390)
- Sensor: Instancias de sensores asignados a motos (UUID PK)
- Lectura: Telemetría en tiempo real (BigInt PK para millones de registros)

Relaciones:
- Sensor → Moto (moto_id: int FK)
- Sensor → Componente (componente_id: int FK, obligatorio en v2.3)
- Sensor → Parametro (parametro_id: int FK, obligatorio en v2.3)
- Lectura → Sensor (sensor_id: UUID FK)

Estados de Sensor:
- ok: Funcionando correctamente
- degraded: Lecturas intermitentes o con errores
- faulty: Mal funcionamiento confirmado
- offline: Sin conexión
- unknown: Estado indeterminado

PKs:
- SensorTemplate: UUID (plantillas reutilizables)
- Sensor: UUID (sensores IoT virtuales)
- Lectura: BIGSERIAL (alta volumetría)

FKs:
- Todos los FKs hacia otros módulos son INT (motos, componentes, parametros)
- sensor_id es UUID (referencia interna de sensores)

Versión: v2.3 MVP
"""
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlalchemy import String, TIMESTAMP, Integer, text, Enum as SQLEnum, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import enum

from ..shared.models import Base

if TYPE_CHECKING:
    from ..motos.models import Componente, Parametro, Moto
    from ..fallas.models import Falla


# ============================================
# CONSTANTES
# ============================================

SQL_NOW = "now()"  # Constante para server_default


# ============================================
# ENUMS
# ============================================

class SensorState(str, enum.Enum):
    """
    Estado de salud del sensor (hardware/conectividad).
    
    Estados:
    - ok: Funcionando correctamente, lecturas válidas
    - degraded: Intermitente, lecturas con errores ocasionales
    - faulty: Mal funcionamiento confirmado, lecturas no confiables
    - offline: Sin conexión, no envía datos
    - unknown: Estado indeterminado, sin lecturas recientes
    """
    OK = "ok"
    DEGRADED = "degraded"
    FAULTY = "faulty"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


# ============================================
# MODELS
# ============================================

class SensorTemplate(Base):
    """
    Plantilla de sensores por modelo de moto.
    
    Define qué sensores deben aprovisionarse automáticamente
    al registrar una moto de un modelo específico.
    
    Ejemplo SEED_DATA_MVP_V2.2.sql:
    - KTM 390 Duke 2024 tiene 11 sensor_templates
    - Cada uno define: tipo, unidad, thresholds, frequency_ms, component_type
    
    Ejemplo definition JSONB:
    {
        "sensor_type": "temperature",
        "unit": "celsius",
        "default_thresholds": {"min": 0, "max": 100},
        "frequency_ms": 1000,
        "component_type": "engine"
    }
    
    Flujo de uso:
    1. Usuario registra moto KTM 390 Duke 2024
    2. Sistema lee sensor_templates para ese modelo
    3. Crea 11 instancias de Sensor basadas en las plantillas
    """
    __tablename__ = "sensor_templates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    modelo: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    definition: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text(SQL_NOW)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text(SQL_NOW),
        onupdate=text(SQL_NOW)
    )

    def __repr__(self):
        return f"<SensorTemplate(id={self.id}, modelo='{self.modelo}', name='{self.name}')>"


class Sensor(Base):
    """
    Sensor instanciado en una moto (gemelo digital).
    
    Cada sensor monitorea un parámetro específico de un componente.
    El sensor_state refleja la salud del sensor mismo (hardware/conectividad).
    
    Cambios v2.3:
    - componente_id: OBLIGATORIO (int FK, antes Optional)
    - parametro_id: OBLIGATORIO (int FK, antes Optional)
    - Razón: Simplifica queries y elimina ambigüedad en lecturas
    
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
        "quality": 0.98,
        "timestamp": "2025-11-10T14:30:00Z"
    }
    
    Flujo de creación:
    1. Usuario registra moto KTM 390 Duke 2024
    2. MotoService.provision_estados_iniciales() crea 11 sensores
    3. Cada sensor vinculado a: moto_id, componente_id, parametro_id
    4. Estado inicial: sensor_state = UNKNOWN (sin lecturas aún)
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
    parametro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parametros.id"),
        nullable=False,
        index=True
    )
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False,
        index=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    sensor_state: Mapped[SensorState] = mapped_column(
        SQLEnum(SensorState, name="sensor_state_enum", values_callable=lambda obj: [e.value for e in obj]),  # type: ignore[arg-type]
        nullable=False,
        server_default=SensorState.UNKNOWN.value
    )
    last_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text(SQL_NOW)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text(SQL_NOW),
        onupdate=text(SQL_NOW)
    )

    # Relaciones
    moto: Mapped["Moto"] = relationship("Moto", back_populates="sensores")
    template: Mapped[Optional["SensorTemplate"]] = relationship("SensorTemplate")
    componente: Mapped["Componente"] = relationship("Componente")
    parametro: Mapped["Parametro"] = relationship("Parametro")
    lecturas: Mapped[list["Lectura"]] = relationship("Lectura", back_populates="sensor", cascade="all, delete-orphan")
    fallas: Mapped[list["Falla"]] = relationship(
        "Falla", back_populates="sensor", cascade="all, delete-orphan"
    )

    @property
    def is_healthy(self) -> bool:
        """Sensor en estado saludable (ok)."""
        return self.sensor_state == SensorState.OK

    @property
    def needs_attention(self) -> bool:
        """Sensor requiere atención (degraded, faulty, offline)."""
        return self.sensor_state in [SensorState.DEGRADED, SensorState.FAULTY, SensorState.OFFLINE]

    def __repr__(self):
        return f"<Sensor(id={self.id}, tipo='{self.tipo}', state={self.sensor_state.value})>"


class Lectura(Base):
    """
    Lectura de telemetría de un sensor.
    
    Almacena las lecturas en tiempo real del gemelo digital.
    Esquema optimizado para MVP. En producción considerar:
    - TimescaleDB (hypertables)
    - Particionado por fecha
    - Compresión automática
    
    Cambios v2.3:
    - componente_id: OBLIGATORIO (int, antes Optional)
    - parametro_id: OBLIGATORIO (int, antes Optional)
    - Razón: Elimina ambigüedad, queries más rápidas sin JOINs innecesarios
    
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
        "source": "websocket",
        "batch_id": "batch-123"
    }
    
    Flujo de inserción:
    1. Frontend envía lectura vía WebSocket
    2. Backend valida y crea Lectura
    3. MotoService.procesar_lectura_y_actualizar_estado()
       - Evalúa reglas de estado
       - Actualiza estado_actual
       - Emite eventos si cambió estado
    
    Volumetría estimada:
    - 1 moto × 11 sensores × 1 lectura/5seg = ~190k lecturas/día
    - 10 motos activas = 1.9M lecturas/día
    - BigInt PK soporta 9 quintillones de registros
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
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id"),
        nullable=False
    )
    parametro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parametros.id"),
        nullable=False
    )
    
    ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True
    )
    valor: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text(SQL_NOW)
    )

    # Relaciones
    moto: Mapped["Moto"] = relationship("Moto", back_populates="lecturas")
    sensor: Mapped["Sensor"] = relationship("Sensor", back_populates="lecturas")
    componente: Mapped["Componente"] = relationship("Componente")
    parametro: Mapped["Parametro"] = relationship("Parametro")

    def __repr__(self):
        val = self.valor.get("value", "?") if self.valor else "?"
        return f"<Lectura(id={self.id}, sensor_id={self.sensor_id}, valor={val}, ts={self.ts})>"
