"""
Modelos de base de datos para suscripciones.
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Date,
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


# ------------------------------------------------------------------
# MÓDULO: SUSCRIPCIONES Y SISTEMA FREEMIUM v2.3
# ------------------------------------------------------------------
# Implementa el sistema de planes (Free/Pro) con control de límites
# mensuales para características premium.
#
# Tablas principales:
# - planes: Free ($0) y Pro ($29.99/mes)
# - caracteristicas: Features con límites por plan (limite_free, limite_pro)
# - suscripciones: Relación usuario <-> plan (1 a 1)
# - uso_caracteristicas: Control de uso mensual con reset automático
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
    """Tabla `caracteristicas` - funcionalidades/características disponibles por plan.
    
    Almacena los límites mensuales por plan (v2.3 Freemium).
    - limite_free = NULL: ilimitado en Free
    - limite_free = 0: bloqueado en Free
    - limite_free > 0: cantidad máxima de usos mensuales en Free
    """

    __tablename__ = "caracteristicas"

    clave_funcion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Clave funcional de la característica, ej: CHATBOT, ML_PREDICTIONS"
    )

    descripcion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción de la característica"
    )

    limite_free: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Límite mensual para usuarios Free. NULL=ilimitado, 0=bloqueado, >0=cantidad de usos/mes"
    )

    limite_pro: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Límite mensual para usuarios Pro. NULL=ilimitado, 0=bloqueado, >0=cantidad de usos/mes"
    )

    # Relaciones
    planes = relationship(
        "Plan",
        secondary="plan_caracteristicas",
        back_populates="caracteristicas",
    )

    usos = relationship(
        "UsoCaracteristica",
        back_populates="caracteristica",
        cascade="all, delete-orphan",
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
    """Tabla `suscripciones` - relación usuario <-> plan.

    Esta clase representa la suscripción asignada a un usuario.
    Constraint: Un usuario solo puede tener UNA suscripción activa (UNIQUE en usuario_id).
    """

    __tablename__ = "suscripciones"
    __table_args__ = (
        CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="ck_suscripcion_fecha_fin"),
    )

    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        unique=True,  # Un usuario solo puede tener una suscripción
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

    # Relaciones
    plan = relationship("Plan", back_populates="suscripciones")
    usuario = relationship("Usuario")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<Suscripcion usuario_id={self.usuario_id} plan_id={self.plan_id} estado={self.estado_suscripcion}>"


class UsoCaracteristica(BaseModel):
    """Tabla `uso_caracteristicas` - control de límites mensuales por usuario.
    
    Registra el uso de características con límites (v2.3 Freemium).
    
    Ejemplos:
    - CHATBOT: limite_mensual=5, usos_realizados=2 → quedan 3 usos
    - ML_PREDICTIONS: limite_mensual=4, usos_realizados=4 → límite alcanzado
    
    El periodo se resetea automáticamente el día 1 de cada mes.
    """

    __tablename__ = "uso_caracteristicas"
    __table_args__ = (
        UniqueConstraint("usuario_id", "caracteristica_id", "periodo_mes", name="uk_uso_usuario_feature_periodo"),
        CheckConstraint("usos_realizados >= 0", name="chk_usos_no_negativos"),
        CheckConstraint("limite_mensual > 0", name="chk_limite_positivo"),
    )

    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID del usuario",
    )

    caracteristica_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("caracteristicas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID de la característica",
    )

    periodo_mes: Mapped[date] = mapped_column(
        Date,  # DATE en SQL, truncado al primer día del mes
        nullable=False,
        comment="Primer día del mes (ej: 2025-11-01 para noviembre). Se usa para agrupar por periodo.",
    )

    usos_realizados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Contador de usos en el periodo actual",
    )

    limite_mensual: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Límite máximo de usos para el periodo (copiado desde caracteristicas.limite_free/pro)",
    )

    ultimo_uso_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp del último uso registrado",
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp",
    )

    # Relaciones
    usuario = relationship("Usuario")
    caracteristica = relationship("Caracteristica", back_populates="usos")

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return (
            f"<UsoCaracteristica usuario_id={self.usuario_id} "
            f"caracteristica_id={self.caracteristica_id} "
            f"periodo={self.periodo_mes.strftime('%Y-%m')} "
            f"usos={self.usos_realizados}/{self.limite_mensual}>"
        )

