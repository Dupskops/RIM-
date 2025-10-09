"""
Esquemas Pydantic para validación de fallas.
Define la estructura de datos para requests y responses.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from ..shared.constants import TipoFalla, SeveridadFalla, EstadoFalla
from ..shared.base_models import FilterParams


# ============================================
# FILTROS
# ============================================

class FallaFilterParams(FilterParams):
    """Parámetros de filtrado para fallas."""
    
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    tipo: Optional[str] = Field(None, description="Filtrar por tipo de falla")
    severidad: Optional[str] = Field(None, description="Filtrar por severidad")
    estado: Optional[str] = Field(None, description="Filtrar por estado")
    origen_deteccion: Optional[str] = Field(None, description="Filtrar por origen (sensor, ml, manual, sistema)")
    
    solo_activas: Optional[bool] = Field(None, description="Solo fallas no resueltas")
    solo_criticas: Optional[bool] = Field(None, description="Solo fallas críticas")
    requiere_atencion_inmediata: Optional[bool] = Field(None, description="Solo fallas urgentes")
    
    fecha_desde: Optional[date] = Field(None, description="Fecha de detección desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha de detección hasta")


# ============================================
# SCHEMAS DE REQUEST
# ============================================

class FallaCreate(BaseModel):
    """Schema para crear una nueva falla."""
    
    moto_id: int = Field(..., description="ID de la moto")
    sensor_id: Optional[int] = Field(None, description="ID del sensor (opcional)")
    
    tipo: str = Field(..., description="Tipo de falla")
    titulo: str = Field(..., min_length=5, max_length=200, description="Título descriptivo")
    descripcion: str = Field(..., min_length=10, description="Descripción detallada")
    severidad: str = Field(default=SeveridadFalla.MEDIA.value, description="Severidad de la falla")
    
    origen_deteccion: str = Field(default="manual", description="Origen: sensor, ml, manual, sistema")
    
    valor_actual: Optional[float] = Field(None, description="Valor actual del sensor")
    valor_esperado: Optional[float] = Field(None, description="Valor esperado")
    
    requiere_atencion_inmediata: bool = Field(default=False, description="¿Requiere atención urgente?")
    puede_conducir: bool = Field(default=True, description="¿Es seguro conducir?")
    
    solucion_sugerida: Optional[str] = Field(None, description="Solución sugerida")
    
    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, v: str) -> str:
        """Valida que el tipo sea válido."""
        try:
            TipoFalla(v)
            return v
        except ValueError:
            raise ValueError(
                f"Tipo de falla inválido: {v}. "
                f"Valores permitidos: {[t.value for t in TipoFalla]}"
            )
    
    @field_validator("severidad")
    @classmethod
    def validate_severidad(cls, v: str) -> str:
        """Valida que la severidad sea válida."""
        try:
            SeveridadFalla(v)
            return v
        except ValueError:
            raise ValueError(
                f"Severidad inválida: {v}. "
                f"Valores permitidos: {[s.value for s in SeveridadFalla]}"
            )
    
    @field_validator("titulo")
    @classmethod
    def validate_titulo(cls, v: str) -> str:
        """Sanitiza el título."""
        return v.strip()
    
    @field_validator("descripcion")
    @classmethod
    def validate_descripcion(cls, v: str) -> str:
        """Sanitiza la descripción."""
        return v.strip()


class FallaMLCreate(BaseModel):
    """Schema para crear falla detectada por ML."""
    
    moto_id: int
    sensor_id: Optional[int] = None
    tipo: str
    titulo: str
    descripcion: str
    severidad: str = SeveridadFalla.MEDIA.value
    
    # Datos específicos de ML
    confianza_ml: float = Field(..., ge=0.0, le=1.0, description="Confianza del modelo (0-1)")
    modelo_ml_usado: str = Field(..., description="Nombre del modelo ML")
    prediccion_ml: Optional[str] = Field(None, description="Detalles de predicción (JSON)")
    
    valor_actual: Optional[float] = None
    valor_esperado: Optional[float] = None
    
    requiere_atencion_inmediata: bool = False
    puede_conducir: bool = True
    solucion_sugerida: Optional[str] = None


class FallaUpdate(BaseModel):
    """Schema para actualizar una falla existente."""
    
    estado: Optional[str] = Field(None, description="Nuevo estado")
    severidad: Optional[str] = Field(None, description="Nueva severidad")
    
    solucion_aplicada: Optional[str] = Field(None, description="Solución que se aplicó")
    costo_real: Optional[float] = Field(None, ge=0, description="Costo real de reparación")
    
    notas_tecnico: Optional[str] = Field(None, description="Notas del técnico")
    
    @field_validator("estado")
    @classmethod
    def validate_estado(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el estado sea válido."""
        if v is None:
            return v
        try:
            EstadoFalla(v)
            return v
        except ValueError:
            raise ValueError(
                f"Estado inválido: {v}. "
                f"Valores permitidos: {[e.value for e in EstadoFalla]}"
            )


class FallaDiagnosticar(BaseModel):
    """Schema para diagnosticar una falla."""
    
    solucion_sugerida: str = Field(..., min_length=10, description="Solución propuesta")
    costo_estimado: Optional[float] = Field(None, ge=0, description="Costo estimado")
    notas_tecnico: Optional[str] = Field(None, description="Notas del diagnóstico")


class FallaResolver(BaseModel):
    """Schema para marcar falla como resuelta."""
    
    solucion_aplicada: str = Field(..., min_length=10, description="Qué se hizo para resolver")
    costo_real: float = Field(..., ge=0, description="Costo real")
    notas_tecnico: Optional[str] = Field(None, description="Notas finales")


# ============================================
# SCHEMAS DE RESPONSE
# ============================================

class FallaResponse(BaseModel):
    """Schema de respuesta con información completa de falla."""
    
    id: int
    moto_id: int
    sensor_id: Optional[int]
    usuario_id: Optional[int]
    
    codigo: str
    tipo: str
    titulo: str
    descripcion: str
    severidad: str
    estado: str
    
    origen_deteccion: str
    
    valor_actual: Optional[float]
    valor_esperado: Optional[float]
    confianza_ml: Optional[float]
    modelo_ml_usado: Optional[str]
    
    requiere_atencion_inmediata: bool
    puede_conducir: bool
    
    solucion_sugerida: Optional[str]
    solucion_aplicada: Optional[str]
    
    fecha_deteccion: datetime
    fecha_diagnostico: Optional[datetime]
    fecha_resolucion: Optional[datetime]
    
    costo_estimado: Optional[float]
    costo_real: Optional[float]
    
    notas_tecnico: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FallaListResponse(BaseModel):
    """Schema de respuesta resumida para listados."""
    
    id: int
    moto_id: int
    codigo: str
    tipo: str
    titulo: str
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
    
    total_fallas: int
    fallas_activas: int
    fallas_resueltas: int
    fallas_criticas: int
    
    por_tipo: dict[str, int]
    por_severidad: dict[str, int]
    por_estado: dict[str, int]
    
    tiempo_promedio_resolucion_dias: Optional[float]
    costo_total_reparaciones: float
    
    tasa_resolucion: float  # Porcentaje de fallas resueltas


class FallaPredictionResponse(BaseModel):
    """Respuesta de predicción de fallas (ML - Premium)."""
    
    moto_id: int
    probabilidad_falla: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de falla (0-1)")
    
    fallas_predichas: list[dict] = Field(
        ...,
        description="Lista de fallas potenciales con probabilidades"
    )
    
    componentes_riesgo: list[dict] = Field(
        ...,
        description="Componentes en riesgo con scores"
    )
    
    recomendaciones: list[str] = Field(
        ...,
        description="Recomendaciones de mantenimiento preventivo"
    )
    
    confianza_prediccion: float = Field(..., ge=0.0, le=1.0)
    fecha_prediccion: datetime
