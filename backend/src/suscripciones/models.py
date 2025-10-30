"""
Modelos de base de datos para suscripciones.
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from src.shared.models import BaseModel


# NOTE: La implementación de suscripciones del MÓDULO 2 utiliza la clase `Suscripcion`
# mapeada a la tabla `suscripciones_usuario`. Esto unifica la representación de una
# suscripción por usuario y evita ambigüedad con antiguas representaciones.


# ------------------------------------------------------------------
# MÓDULO 2: FREEMIUM Y SUSCRIPCIONES (migrado desde docs/SCRIPT.SQL)
# ------------------------------------------------------------------


class PeriodoPlan(str, Enum):
    """Periodo de facturación para un plan."""
    MENSUAL = "mensual"
    ANUAL = "anual"
    UNICO = "unico"


class EstadoSuscripcion(str, Enum):
    """Estado de suscripción (tabla suscripciones_usuario)."""
    ACTIVA = "activa"
    CANCELADA = "cancelada"
    PENDIENTE_PAGO = "pendiente_pago"


class Plan(BaseModel):
    """Tabla `planes` - define planes y precios."""

    __tablename__ = "planes"

    nombre_plan: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Nombre del plan"
    )

    precio: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True),
        nullable=False,
        default=Decimal("0.00"),
        comment="Precio del plan"
    )

    periodo_facturacion: Mapped[PeriodoPlan] = mapped_column(
        SQLEnum(PeriodoPlan, native_enum=True),
        default=PeriodoPlan.UNICO,
        nullable=False,
        comment="Periodo de facturación"
    )

    # Relaciones
    caracteristicas = relationship(
        "Caracteristica",
        secondary="plan_caracteristicas",
        back_populates="planes",
    )

    suscripciones = relationship(
        "Suscripcion",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class Caracteristica(BaseModel):
    """Tabla `caracteristicas` - funcionalidades/características disponibles por plan."""

    __tablename__ = "caracteristicas"

    clave_funcion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Clave funcional de la característica, ej: CHAT_LLM"
    )

    descripcion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción de la característica"
    )

    # Relaciones
    planes = relationship(
        "Plan",
        secondary="plan_caracteristicas",
        back_populates="caracteristicas",
    )


class PlanCaracteristica(BaseModel):
    """Tabla de unión `plan_caracteristicas`.

    Nota: en el script SQL original la PK es compuesta (plan_id, caracteristica_id).
    Aquí mantenemos un id por compatibilidad con el `BaseModel` pero aseguramos
    unicidad con una constraint única.
    """

    __tablename__ = "plan_caracteristicas"
    __table_args__ = (
        UniqueConstraint("plan_id", "caracteristica_id", name="uq_plan_caracteristica"),
    )

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("planes.id"),
        nullable=False,
        index=True,
        comment="FK a planes"
    )

    caracteristica_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("caracteristicas.id"),
        nullable=False,
        index=True,
        comment="FK a caracteristicas"
    )


class Suscripcion(BaseModel):
    """Tabla `suscripciones_usuario` - relación usuario <-> plan.

    Esta clase representa la suscripción asignada a un usuario y está mapeada
    a la tabla `suscripciones_usuario` en la base de datos.
    """

    __tablename__ = "suscripciones_usuario"

    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
        comment="ID del usuario",
    )

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("planes.id"),
        nullable=False,
        index=True,
        comment="FK al plan asignado",
    )

    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Fecha de inicio de la suscripción",
    )

    fecha_fin: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fecha de fin (nulo si vitalicio o free)",
    )

    estado_suscripcion: Mapped[EstadoSuscripcion] = mapped_column(
        SQLEnum(EstadoSuscripcion, native_enum=True),
        nullable=False,
        default=EstadoSuscripcion.ACTIVA,
        comment="Estado de la suscripción",
    )

    __table_args__ = (
        CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="ck_suscripcion_fecha_fin"),
    )

    # Relaciones
    plan = relationship("Plan", back_populates="suscripciones")
    usuario = relationship("Usuario")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Suscripcion usuario_id={self.usuario_id} plan_id={self.plan_id} estado={self.estado_suscripcion}>"

