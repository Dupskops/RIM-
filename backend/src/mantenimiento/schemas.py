"""
Esquemas Pydantic para validación de datos de mantenimiento.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from src.shared.constants import TipoMantenimiento, EstadoMantenimiento
from src.shared.base_models import FilterParams


# ============================================
# REQUEST SCHEMAS
# ============================================

class MantenimientoCreate(BaseModel):
    """Esquema para crear un mantenimiento."""
    moto_id: int = Field(..., gt=0, description="ID de la moto")
    tipo: TipoMantenimiento = Field(..., description="Tipo de mantenimiento")
    descripcion: str = Field(..., min_length=10, max_length=1000, description="Descripción del mantenimiento")
    
    es_preventivo: bool = Field(default=True, description="Es mantenimiento preventivo o correctivo")
    falla_relacionada_id: Optional[int] = Field(None, gt=0, description="ID de falla relacionada (si es correctivo)")
    
    kilometraje_actual: int = Field(..., ge=0, description="Kilometraje actual")
    kilometraje_siguiente: Optional[int] = Field(None, ge=0, description="Kilometraje para próximo servicio")
    
    fecha_programada: Optional[date] = Field(None, description="Fecha programada del servicio")
    fecha_vencimiento: Optional[date] = Field(None, description="Fecha límite del servicio")
    
    mecanico_asignado: Optional[str] = Field(None, max_length=100, description="Nombre del mecánico")
    taller_realizado: Optional[str] = Field(None, max_length=200, description="Taller donde se realizará")
    
    costo_estimado: Optional[float] = Field(None, ge=0, description="Costo estimado")
    prioridad: int = Field(default=3, ge=1, le=5, description="Prioridad (1-5)")
    es_urgente: bool = Field(default=False, description="Marca como urgente")
    dias_anticipacion_alerta: int = Field(default=7, ge=1, le=30, description="Días de anticipación para alerta")

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: TipoMantenimiento) -> TipoMantenimiento:
        """Valida que el tipo sea válido."""
        if v not in TipoMantenimiento:
            raise ValueError(f"Tipo de mantenimiento inválido: {v}")
        return v

    @field_validator("kilometraje_siguiente")
    @classmethod
    def validate_kilometraje_siguiente(cls, v: Optional[int], info) -> Optional[int]:
        """Valida que el kilometraje siguiente sea mayor al actual."""
        if v is not None and "kilometraje_actual" in info.data:
            if v <= info.data["kilometraje_actual"]:
                raise ValueError("El kilometraje siguiente debe ser mayor al actual")
        return v


class MantenimientoMLCreate(BaseModel):
    """Esquema para crear mantenimiento recomendado por IA."""
    moto_id: int = Field(..., gt=0)
    tipo: TipoMantenimiento
    descripcion: str = Field(..., min_length=10, max_length=1000)
    kilometraje_actual: int = Field(..., ge=0)
    
    # Campos específicos de ML
    confianza_prediccion: float = Field(..., ge=0.0, le=1.0, description="Confianza de la predicción")
    modelo_ia_usado: str = Field(..., max_length=100, description="Modelo usado para la predicción")
    
    # Opcionales
    fecha_vencimiento: Optional[date] = None
    prioridad: int = Field(default=3, ge=1, le=5)
    es_urgente: bool = Field(default=False)


class MantenimientoUpdate(BaseModel):
    """Esquema para actualizar un mantenimiento."""
    tipo: Optional[TipoMantenimiento] = None
    estado: Optional[EstadoMantenimiento] = None
    descripcion: Optional[str] = Field(None, min_length=10, max_length=1000)
    notas_tecnico: Optional[str] = Field(None, max_length=2000)
    
    mecanico_asignado: Optional[str] = Field(None, max_length=100)
    taller_realizado: Optional[str] = Field(None, max_length=200)
    
    fecha_programada: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    
    prioridad: Optional[int] = Field(None, ge=1, le=5)
    es_urgente: Optional[bool] = None
    dias_anticipacion_alerta: Optional[int] = Field(None, ge=1, le=30)


class MantenimientoIniciar(BaseModel):
    """Esquema para iniciar un mantenimiento."""
    mecanico_asignado: Optional[str] = Field(None, max_length=100)
    taller_realizado: Optional[str] = Field(None, max_length=200)
    notas_tecnico: Optional[str] = Field(None, max_length=2000)


class MantenimientoCompletar(BaseModel):
    """Esquema para completar un mantenimiento."""
    notas_tecnico: str = Field(..., min_length=10, max_length=2000, description="Notas del técnico")
    repuestos_usados: Optional[str] = Field(None, max_length=2000, description="Repuestos utilizados")
    
    kilometraje_siguiente: Optional[int] = Field(None, ge=0, description="Próximo mantenimiento (km)")
    
    costo_real: float = Field(..., ge=0, description="Costo real total")
    costo_repuestos: Optional[float] = Field(None, ge=0, description="Costo de repuestos")
    costo_mano_obra: Optional[float] = Field(None, ge=0, description="Costo de mano de obra")


# ============================================
# RESPONSE SCHEMAS
# ============================================

class MantenimientoResponse(BaseModel):
    """Esquema de respuesta de mantenimiento."""
    id: int
    codigo: str
    moto_id: int
    
    tipo: TipoMantenimiento
    estado: EstadoMantenimiento
    es_preventivo: bool
    falla_relacionada_id: Optional[int]
    
    kilometraje_actual: int
    kilometraje_siguiente: Optional[int]
    
    fecha_programada: Optional[date]
    fecha_inicio: Optional[datetime]
    fecha_completado: Optional[datetime]
    fecha_vencimiento: Optional[date]
    
    descripcion: str
    notas_tecnico: Optional[str]
    repuestos_usados: Optional[str]
    
    mecanico_asignado: Optional[str]
    taller_realizado: Optional[str]
    
    costo_estimado: Optional[float]
    costo_real: Optional[float]
    costo_repuestos: Optional[float]
    costo_mano_obra: Optional[float]
    
    prioridad: int
    es_urgente: bool
    dias_anticipacion_alerta: int
    alerta_enviada: bool
    
    recomendado_por_ia: bool
    confianza_prediccion: Optional[float]
    modelo_ia_usado: Optional[str]
    
    # Propiedades calculadas
    esta_completado: bool
    esta_vencido: bool
    dias_hasta_vencimiento: Optional[int]
    requiere_atencion: bool
    costo_total: Optional[float]
    duracion_servicio: Optional[int]
    
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MantenimientoFilterParams(FilterParams):
    """Parámetros de filtrado para mantenimientos."""
    moto_id: Optional[int] = Field(None, gt=0, description="Filtrar por moto")
    tipo: Optional[TipoMantenimiento] = Field(None, description="Filtrar por tipo de mantenimiento")
    estado: Optional[EstadoMantenimiento] = Field(None, description="Filtrar por estado")
    es_preventivo: Optional[bool] = Field(None, description="Filtrar por preventivo/correctivo")
    es_urgente: Optional[bool] = Field(None, description="Filtrar solo urgentes")
    solo_activos: Optional[bool] = Field(None, description="Filtrar solo activos (pendientes, programados, en proceso)")
    solo_vencidos: Optional[bool] = Field(None, description="Filtrar solo vencidos")
    fecha_desde: Optional[date] = Field(None, description="Filtrar desde fecha")
    fecha_hasta: Optional[date] = Field(None, description="Filtrar hasta fecha")
    recomendado_por_ia: Optional[bool] = Field(None, description="Filtrar solo recomendados por IA")


class MantenimientoStatsResponse(BaseModel):
    """Esquema de respuesta para estadísticas de mantenimiento."""
    total_mantenimientos: int
    pendientes: int
    programados: int
    en_proceso: int
    completados: int
    cancelados: int
    vencidos: int
    urgentes: int
    
    # Por tipo
    por_tipo: dict[str, int]
    
    # Costos
    costo_total_estimado: float
    costo_total_real: float
    costo_promedio: float
    
    # Tiempos
    duracion_promedio_horas: Optional[float]
    
    # IA
    recomendados_por_ia: int
    confianza_promedio_ia: Optional[float]


class MantenimientoHistorialResponse(BaseModel):
    """Esquema de respuesta para historial de mantenimientos."""
    moto_id: int
    total: int
    ultimo_mantenimiento: Optional[MantenimientoResponse]
    proximo_recomendado: Optional[date]
    items: List[MantenimientoResponse]
