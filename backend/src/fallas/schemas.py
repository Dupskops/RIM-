"""
Esquemas Pydantic para validación de fallas.
MVP v2.3 - Schema simplificado sin campos ML/diagnostic
"""
from datetime import datetime, date
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator

from .models import SeveridadFalla, EstadoFalla, OrigenDeteccion


# ============================================
# FILTROS
# ============================================

class FallaFilterParams(BaseModel):
    """Parámetros de filtrado para fallas."""
    
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    tipo: Optional[str] = Field(None, description="Filtrar por tipo de falla")
    severidad: Optional[SeveridadFalla] = Field(None, description="Filtrar por severidad")
    estado: Optional[EstadoFalla] = Field(None, description="Filtrar por estado")
    origen_deteccion: Optional[OrigenDeteccion] = Field(None, description="Filtrar por origen")
    
    solo_activas: Optional[bool] = Field(None, description="Solo fallas no resueltas")
    solo_criticas: Optional[bool] = Field(None, description="Solo fallas críticas")
    requiere_atencion_inmediata: Optional[bool] = Field(None, description="Solo fallas urgentes")
    
    fecha_desde: Optional[date] = Field(None, description="Fecha de detección desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de detección hasta")


# ============================================
# SCHEMAS DE REQUEST
# ============================================

class FallaCreate(BaseModel):
    """Schema para crear una nueva falla (MVP v2.3)."""
    
    moto_id: int = Field(..., description="ID de la moto")
    componente_id: int = Field(..., description="ID del componente afectado")
    
    tipo: str = Field(..., description="Tipo de falla (string libre)")
    descripcion: Optional[str] = Field(None, description="Descripción detallada (opcional)")
    severidad: SeveridadFalla = Field(default=SeveridadFalla.MEDIA, description="Severidad de la falla")
    
    origen_deteccion: Optional[OrigenDeteccion] = Field(
        default=OrigenDeteccion.MANUAL, 
        description="Origen de detección"
    )
    
    latitud: Optional[float] = Field(None, description="Latitud GPS donde se detectó")
    longitud: Optional[float] = Field(None, description="Longitud GPS donde se detectó")
    
    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        """Valida que el tipo no esté vacío (tipo es string libre en v2.3)."""
        if not v or not v.strip():
            raise ValueError("El tipo de falla no puede estar vacío")
        return v.strip().lower()


class FallaUpdate(BaseModel):
    """
    Schema para actualizar una falla existente (MVP v2.3).
    
    Campos editables:
    - descripcion
    - severidad
    - solucion_sugerida
    - latitud/longitud
    
    NO se edita el estado (usar endpoints específicos para eso)
    """
    
    descripcion: Optional[str] = Field(None, description="Nueva descripción")
    severidad: Optional[SeveridadFalla] = Field(None, description="Nueva severidad")
    solucion_sugerida: Optional[str] = Field(None, description="Actualizar solución sugerida")
    latitud: Optional[float] = Field(None, description="Actualizar latitud")
    longitud: Optional[float] = Field(None, description="Actualizar longitud")


# ============================================
# SCHEMAS DE RESPONSE
# ============================================

class FallaResponse(BaseModel):
    """Schema de respuesta con información completa de falla (MVP v2.3)."""
    
    id: int
    moto_id: int
    componente_id: int
    
    codigo: str
    tipo: str
    descripcion: Optional[str]
    severidad: str
    estado: str
    
    origen_deteccion: str
    
    requiere_atencion_inmediata: bool
    puede_conducir: bool
    
    solucion_sugerida: Optional[str]
    
    latitud: Optional[float]
    longitud: Optional[float]
    
    fecha_deteccion: datetime
    fecha_resolucion: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FallaListResponse(BaseModel):
    """Schema de respuesta resumida para listados."""
    
    id: int
    moto_id: int
    componente_id: int
    codigo: str
    tipo: str
    descripcion: Optional[str]
    severidad: str
    estado: str
    origen_deteccion: str
    requiere_atencion_inmediata: bool
    puede_conducir: bool
    fecha_deteccion: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class FallaStatsResponse(BaseModel):
    """Estadísticas de fallas (Premium)."""
    
    total: int
    activas: int
    resueltas: int
    criticas: int
    
    por_tipo: Dict[str, int]
    por_severidad: Dict[str, int]
    por_estado: Dict[str, int]
    
    tiempo_promedio_resolucion: float  # En días
    
    class Config:
        from_attributes = True
