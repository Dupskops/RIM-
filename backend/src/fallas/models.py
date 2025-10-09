"""
Modelos de base de datos para el módulo de fallas.
Representa fallas detectadas en las motos y su tracking.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..shared.models import BaseModel
from ..shared.constants import TipoFalla, SeveridadFalla, EstadoFalla


class Falla(BaseModel):
    """
    Modelo de falla detectada en una moto.
    
    Representa una anomalía o problema identificado por:
    - Sensores IoT (lecturas fuera de rango)
    - ML/IA (detección predictiva)
    - Usuario (reporte manual)
    """
    
    __tablename__ = "fallas"
    
    # Relaciones
    moto_id: Mapped[int] = mapped_column(Integer, ForeignKey("motos.id"), nullable=False)
    sensor_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("sensores.id"), 
        nullable=True,
        comment="Sensor que detectó la falla (si aplica)"
    )
    usuario_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        comment="Usuario que reportó la falla (si es manual)"
    )
    
    # Información de la falla
    codigo: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Código único de la falla (ej: FL-20250107-001)"
    )
    
    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tipo de falla (sobrecalentamiento, bateria_baja, etc.)"
    )
    
    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Título descriptivo de la falla"
    )
    
    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción detallada de la falla"
    )
    
    severidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SeveridadFalla.MEDIA.value,
        comment="Severidad: baja, media, alta, critica"
    )
    
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoFalla.DETECTADA.value,
        comment="Estado: detectada, diagnosticada, en_reparacion, resuelta"
    )
    
    # Origen de detección
    origen_deteccion: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Origen: sensor, ml, manual, sistema"
    )
    
    # Datos técnicos
    valor_actual: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Valor del sensor al momento de detectar la falla"
    )
    
    valor_esperado: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Valor esperado del sensor"
    )
    
    confianza_ml: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confianza del modelo ML (0.0 a 1.0)"
    )
    
    # Información de ML
    modelo_ml_usado: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nombre del modelo ML que detectó la falla"
    )
    
    prediccion_ml: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detalles de la predicción ML (JSON)"
    )
    
    # Resolución
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
    
    solucion_aplicada: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Solución que se aplicó realmente"
    )
    
    # Fechas
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Cuándo se detectó la falla"
    )
    
    fecha_diagnostico: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Cuándo se diagnosticó la falla"
    )
    
    fecha_resolucion: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Cuándo se resolvió la falla"
    )
    
    # Costos
    costo_estimado: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Costo estimado de reparación"
    )
    
    costo_real: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Costo real de reparación"
    )
    
    # Notas adicionales
    notas_tecnico: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas del técnico que diagnosticó/reparó"
    )
    
    # Relaciones SQLAlchemy
    moto = relationship("Moto", back_populates="fallas")
    sensor = relationship("Sensor", back_populates="fallas")
    usuario = relationship("Usuario", back_populates="fallas_reportadas")
    mantenimientos = relationship("Mantenimiento", back_populates="falla_relacionada")
    
    def __repr__(self) -> str:
        return (
            f"<Falla {self.codigo} | "
            f"Moto: {self.moto_id} | "
            f"Tipo: {self.tipo} | "
            f"Severidad: {self.severidad}>"
        )
    
    @property
    def esta_resuelta(self) -> bool:
        """Verifica si la falla está resuelta."""
        return self.estado == EstadoFalla.RESUELTA.value
    
    @property
    def dias_sin_resolver(self) -> int:
        """Calcula días desde la detección sin resolver."""
        if self.esta_resuelta:
            return 0
        delta = datetime.utcnow() - self.fecha_deteccion
        return delta.days
    
    @property
    def es_critica(self) -> bool:
        """Verifica si es una falla crítica."""
        return self.severidad == SeveridadFalla.CRITICA.value
