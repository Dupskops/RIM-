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
        SQLEnum(TipoMantenimiento, name="tipo_mantenimiento", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    estado: Mapped[EstadoMantenimiento] = mapped_column(
        SQLEnum(EstadoMantenimiento, name="estado_mantenimiento", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EstadoMantenimiento.PENDIENTE,
        index=True
    )
    
    # Origen del mantenimiento (falla relacionada)
    falla_relacionada_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("fallas.id"), 
        nullable=True
    )
    
    # Kilometraje
    kilometraje_actual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    kilometraje_siguiente: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Fechas
    fecha_programada: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_completado: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Detalles del servicio
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notas_tecnico: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Costos
    costo_estimado: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    costo_real: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relaciones
    moto = relationship("Moto", back_populates="mantenimientos")
    falla_relacionada = relationship("Falla", back_populates="mantenimientos")

    @property
    def esta_completado(self) -> bool:
        """Verifica si el mantenimiento está completado."""
        return self.estado == EstadoMantenimiento.COMPLETADO

    @property
    def esta_vencido(self) -> bool:
        """
        Verifica si el mantenimiento está vencido.
        Usa fecha_programada como referencia de vencimiento.
        """
        if not self.fecha_programada:
            return False
        return date.today() > self.fecha_programada and not self.esta_completado

    @property
    def dias_hasta_vencimiento(self) -> Optional[int]:
        """
        Calcula días hasta el vencimiento.
        Usa fecha_programada como referencia.
        """
        if not self.fecha_programada:
            return None
        delta = self.fecha_programada - date.today()
        return delta.days

    @property
    def requiere_atencion(self) -> bool:
        """
        Verifica si requiere atención inmediata.
        Basado en fecha_programada y estado.
        """
        # Requiere atención si está vencido o próximo a vencer (7 días)
        if self.esta_vencido:
            return True
        
        dias = self.dias_hasta_vencimiento
        if dias is not None and dias <= 7:
            return True
        
        # O si está en proceso
        return self.estado == EstadoMantenimiento.EN_PROCESO

    @property
    def costo_total(self) -> Optional[float]:
        """
        Calcula el costo total.
        Prioriza costo_real, luego costo_estimado.
        """
        if self.costo_real is not None:
            return self.costo_real
        return self.costo_estimado

    def __repr__(self) -> str:
        return (
            f"<Mantenimiento(id={self.id}, codigo='{self.codigo}', "
            f"tipo={self.tipo.value}, estado={self.estado.value}, "
            f"moto_id={self.moto_id})>"
        )
