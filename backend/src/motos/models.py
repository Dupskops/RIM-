"""
Modelos de dominio para el módulo de motos.

Jerarquía v2.3:
- ModeloMoto: Catálogo de modelos (KTM 390 Duke 2024, etc.)
- Moto: Instancias de motos registradas por usuarios
- Componente: Componentes por modelo (Motor, Frenos, etc.)
- Parametro: Parámetros medibles (temperatura, presión, etc.)
- ReglaEstado: Umbrales globales por componente-parámetro
- EstadoActual: Estado en tiempo real por moto-componente

Estados:
- EstadoSalud: EXCELENTE, BUENO, ATENCION, CRITICO, FRIO
- LogicaRegla: MAYOR_QUE, MENOR_QUE, ENTRE

PKs: SERIAL (int) para todas las tablas
FKs: Cascadas apropiadas según reglas de negocio
"""
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from decimal import Decimal
import enum
from sqlalchemy import String, Integer, Text, TIMESTAMP, Numeric, Boolean, text
from sqlalchemy import Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from ..shared.models import Base

if TYPE_CHECKING:
    from ..auth.models import Usuario
    from ..sensores.models import Sensor, Lectura
    from ..fallas.models import Falla
    from ..mantenimiento.models import Mantenimiento
    from ..chatbot.models import Conversacion


# ============================================
# ENUMS
# ============================================

class LogicaRegla(str, enum.Enum):
    """Lógica de evaluación de reglas de estado."""
    MAYOR_QUE = "MAYOR_QUE"
    MENOR_QUE = "MENOR_QUE"
    ENTRE = "ENTRE"


class EstadoSalud(str, enum.Enum):
    """Estado de salud de un componente."""
    EXCELENTE = "EXCELENTE"
    BUENO = "BUENO"
    ATENCION = "ATENCION"
    CRITICO = "CRITICO"
    FRIO = "FRIO"  # Sin datos suficientes


# ============================================
# MODELS
# ============================================

class ModeloMoto(Base):
    """
    Catálogo de modelos de motos.
    
    Define los modelos disponibles con sus especificaciones técnicas.
    MVP: KTM 390 Duke 2024
    """
    __tablename__ = "modelos_moto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    marca: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    cilindrada: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tipo_motor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    especificaciones_tecnicas: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    
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
    motos: Mapped[list["Moto"]] = relationship("Moto", back_populates="modelo_moto")
    componentes: Mapped[list["Componente"]] = relationship("Componente", back_populates="modelo_moto")

    def __repr__(self):
        return f"<ModeloMoto(id={self.id}, nombre='{self.nombre}', marca='{self.marca}', año={self.año})>"


class Moto(Base):
    """
    Moto registrada por un usuario.
    
    Cada usuario puede tener múltiples motos (según plan).
    """
    __tablename__ = "motos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    modelo_moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("modelos_moto.id"),
        nullable=False,
        index=True
    )
    vin: Mapped[str] = mapped_column(String(17), nullable=False, unique=True, index=True)
    placa: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kilometraje_actual: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        server_default=text("0")
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="motos")
    modelo_moto: Mapped["ModeloMoto"] = relationship("ModeloMoto", back_populates="motos")
    estados_actuales: Mapped[list["EstadoActual"]] = relationship(
        "EstadoActual", back_populates="moto", cascade="all, delete-orphan"
    )
    sensores: Mapped[list["Sensor"]] = relationship(
        "Sensor", back_populates="moto", cascade="all, delete-orphan"
    )
    lecturas: Mapped[list["Lectura"]] = relationship(
        "Lectura", back_populates="moto", cascade="all, delete-orphan"
    )
    fallas: Mapped[list["Falla"]] = relationship(
        "Falla", back_populates="moto", cascade="all, delete-orphan"
    )
    mantenimientos: Mapped[list["Mantenimiento"]] = relationship(
        "Mantenimiento", back_populates="moto", cascade="all, delete-orphan"
    )
    conversaciones: Mapped[list["Conversacion"]] = relationship(
        "Conversacion", back_populates="moto", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Moto(id={self.id}, vin='{self.vin}', placa='{self.placa}')>"


class Componente(Base):
    """
    Componente por modelo de moto.
    
    Define los componentes medibles de cada modelo.
    KTM 390 Duke 2024: 11 componentes (Motor, Frenos, Cadena, etc.)
    """
    __tablename__ = "componentes"
    __table_args__ = (
        UniqueConstraint('modelo_moto_id', 'nombre', name='uk_componente_modelo_nombre'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    modelo_moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("modelos_moto.id"),
        nullable=False,
        index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    mesh_id_3d: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    modelo_moto: Mapped["ModeloMoto"] = relationship("ModeloMoto", back_populates="componentes")
    reglas_estado: Mapped[list["ReglaEstado"]] = relationship(
        "ReglaEstado", back_populates="componente", cascade="all, delete-orphan"
    )
    estados_actuales: Mapped[list["EstadoActual"]] = relationship(
        "EstadoActual", back_populates="componente", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Componente(id={self.id}, nombre='{self.nombre}')>"


class Parametro(Base):
    """
    Parámetro medible.
    
    Define las métricas que se pueden medir: temperatura, presión, voltaje, etc.
    """
    __tablename__ = "parametros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    unidad_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relaciones
    reglas_estado: Mapped[list["ReglaEstado"]] = relationship(
        "ReglaEstado", back_populates="parametro", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Parametro(id={self.id}, nombre='{self.nombre}', unidad='{self.unidad_medida}')>"


class ReglaEstado(Base):
    """
    Regla de estado global por componente-parámetro.
    
    Define los umbrales para determinar el estado de salud.
    Ejemplo: Motor-Temperatura debe ser MENOR_QUE 95°C (bueno), 105°C (atención), 115°C (crítico)
    """
    __tablename__ = "reglas_estado"
    __table_args__ = (
        UniqueConstraint('componente_id', 'parametro_id', name='uk_regla_componente_parametro'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parametro_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parametros.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    logica: Mapped[LogicaRegla] = mapped_column(
        SQLEnum(LogicaRegla, name="logica_regla", values_callable=lambda obj: [e.value for e in obj]),  # type: ignore[arg-type]
        nullable=False
    )
    limite_bueno: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    limite_atencion: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    limite_critico: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
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
    componente: Mapped["Componente"] = relationship("Componente", back_populates="reglas_estado")
    parametro: Mapped["Parametro"] = relationship("Parametro", back_populates="reglas_estado")

    def __repr__(self):
        return f"<ReglaEstado(componente_id={self.componente_id}, parametro_id={self.parametro_id}, logica={self.logica.value})>"


class EstadoActual(Base):
    """
    Estado actual de un componente en una moto específica.
    
    Refleja el estado de salud calculado en tiempo real.
    Cada moto tiene un estado por cada componente.
    """
    __tablename__ = "estado_actual"
    __table_args__ = (
        UniqueConstraint('moto_id', 'componente_id', name='uk_estado_moto_componente'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    moto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("motos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    componente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("componentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ultimo_valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    estado: Mapped[EstadoSalud] = mapped_column(
        SQLEnum(EstadoSalud, name="estado_componente", values_callable=lambda obj: [e.value for e in obj]),  # type: ignore[arg-type]
        nullable=False,
        index=True
    )
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False
    )

    # Relaciones
    moto: Mapped["Moto"] = relationship("Moto", back_populates="estados_actuales")
    componente: Mapped["Componente"] = relationship("Componente", back_populates="estados_actuales")

    def __repr__(self):
        return f"<EstadoActual(moto_id={self.moto_id}, componente_id={self.componente_id}, estado={self.estado.value})>"

