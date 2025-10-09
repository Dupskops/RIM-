"""
Modelos de base de datos para el módulo de mantenimiento.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models import BaseModel
from src.shared.constants import TipoMantenimiento, EstadoMantenimiento


class Mantenimiento(BaseModel):
    """
    Modelo de mantenimiento programado/realizado.
    
    Representa un servicio de mantenimiento para una motocicleta,
    puede ser preventivo (programado) o correctivo (por falla).
    """
    __tablename__ = "mantenimientos"

    # Identificación (id ya está en BaseModel)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    
    # Relación con moto
    moto_id: Mapped[int] = mapped_column(Integer, ForeignKey("motos.id"), nullable=False, index=True)
    
    # Tipo y estado
    tipo: Mapped[TipoMantenimiento] = mapped_column(
        SQLEnum(TipoMantenimiento, name="tipo_mantenimiento"),
        nullable=False,
        index=True
    )
    estado: Mapped[EstadoMantenimiento] = mapped_column(
        SQLEnum(EstadoMantenimiento, name="estado_mantenimiento"),
        nullable=False,
        default=EstadoMantenimiento.PENDIENTE,
        index=True
    )
    
    # Origen del mantenimiento
    es_preventivo: Mapped[bool] = mapped_column(default=True)
    falla_relacionada_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("fallas.id"), 
        nullable=True
    )
    
    # Kilometraje
    kilometraje_actual: Mapped[int] = mapped_column(Integer, nullable=False)
    kilometraje_siguiente: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Fechas
    fecha_programada: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_inicio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_completado: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Detalles del servicio
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    notas_tecnico: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    repuestos_usados: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Personal
    mecanico_asignado: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    taller_realizado: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Costos
    costo_estimado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    costo_real: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    costo_repuestos: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    costo_mano_obra: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Recordatorios y alertas
    dias_anticipacion_alerta: Mapped[int] = mapped_column(Integer, default=7)
    alerta_enviada: Mapped[bool] = mapped_column(default=False)
    fecha_alerta_enviada: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Prioridad y urgencia
    prioridad: Mapped[int] = mapped_column(Integer, default=3)  # 1-5 (1=baja, 5=crítica)
    es_urgente: Mapped[bool] = mapped_column(default=False)
    
    # ML/IA predictions
    recomendado_por_ia: Mapped[bool] = mapped_column(default=False)
    confianza_prediccion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    modelo_ia_usado: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relaciones
    moto = relationship("Moto", back_populates="mantenimientos")
    falla_relacionada = relationship("Falla", back_populates="mantenimientos")

    @property
    def esta_completado(self) -> bool:
        """Verifica si el mantenimiento está completado."""
        return self.estado == EstadoMantenimiento.COMPLETADO

    @property
    def esta_vencido(self) -> bool:
        """Verifica si el mantenimiento está vencido."""
        if not self.fecha_vencimiento:
            return False
        return date.today() > self.fecha_vencimiento and not self.esta_completado

    @property
    def dias_hasta_vencimiento(self) -> Optional[int]:
        """Calcula días hasta el vencimiento."""
        if not self.fecha_vencimiento:
            return None
        delta = self.fecha_vencimiento - date.today()
        return delta.days

    @property
    def requiere_atencion(self) -> bool:
        """Verifica si requiere atención inmediata."""
        return (
            self.es_urgente or 
            self.prioridad >= 4 or 
            self.esta_vencido or
            (self.dias_hasta_vencimiento is not None and self.dias_hasta_vencimiento <= 0)
        )

    @property
    def duracion_servicio(self) -> Optional[int]:
        """Calcula la duración del servicio en horas."""
        if not self.fecha_inicio or not self.fecha_completado:
            return None
        delta = self.fecha_completado - self.fecha_inicio
        return int(delta.total_seconds() / 3600)

    @property
    def costo_total(self) -> Optional[float]:
        """Calcula el costo total (repuestos + mano de obra)."""
        if self.costo_real is not None:
            return self.costo_real
        if self.costo_repuestos is not None and self.costo_mano_obra is not None:
            return self.costo_repuestos + self.costo_mano_obra
        return self.costo_estimado

    @property
    def variacion_costo(self) -> Optional[float]:
        """Calcula la variación entre costo estimado y real."""
        if not self.costo_estimado or not self.costo_real:
            return None
        return self.costo_real - self.costo_estimado

    @property
    def porcentaje_variacion_costo(self) -> Optional[float]:
        """Calcula el porcentaje de variación de costo."""
        if not self.costo_estimado or not self.costo_real:
            return None
        if self.costo_estimado == 0:
            return None
        return ((self.costo_real - self.costo_estimado) / self.costo_estimado) * 100

    def __repr__(self) -> str:
        return (
            f"<Mantenimiento(id={self.id}, codigo='{self.codigo}', "
            f"tipo={self.tipo.value}, estado={self.estado.value}, "
            f"moto_id={self.moto_id})>"
        )
