"""
Schemas de Pydantic para el módulo de ML.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from src.shared.base_models import FilterParams


# ============= ENUMS =============

class TipoPrediccionEnum(str, Enum):
    """Tipos de predicciones."""
    FALLA = "falla"
    ANOMALIA = "anomalia"
    MANTENIMIENTO = "mantenimiento"
    DESGASTE = "desgaste"


class NivelConfianzaEnum(str, Enum):
    """Niveles de confianza."""
    MUY_BAJO = "muy_bajo"
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    MUY_ALTO = "muy_alto"


class EstadoPrediccionEnum(str, Enum):
    """Estados de predicción."""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    FALSA = "falsa"
    EXPIRADA = "expirada"


# ============= PREDICCION SCHEMAS =============

class DatosSensor(BaseModel):
    """Datos de sensores para predicción."""
    temperatura: Optional[float] = Field(None, ge=-50, le=200, description="Temperatura en °C")
    vibracion: Optional[float] = Field(None, ge=0, le=100, description="Nivel de vibración")
    rpm: Optional[int] = Field(None, ge=0, le=15000, description="Revoluciones por minuto")
    velocidad: Optional[float] = Field(None, ge=0, le=300, description="Velocidad en km/h")
    presion_aceite: Optional[float] = Field(None, ge=0, le=10, description="Presión de aceite en bar")
    nivel_combustible: Optional[float] = Field(None, ge=0, le=100, description="Nivel de combustible %")
    
    @field_validator('temperatura')
    @classmethod
    def validar_temperatura(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < -20 or v > 150):
            raise ValueError("Temperatura fuera de rango normal (-20 a 150°C)")
        return v


class PrediccionFallaRequest(BaseModel):
    """Request para predicción de fallas."""
    moto_id: int = Field(..., gt=0, description="ID de la motocicleta")
    datos_sensor: DatosSensor = Field(..., description="Datos de sensores")
    kilometraje: int = Field(..., ge=0, description="Kilometraje actual")
    dias_ultimo_mantenimiento: int = Field(..., ge=0, description="Días desde último mantenimiento")
    historial_fallas: List[str] = Field(default_factory=list, description="Historial de fallas previas")


class PrediccionAnomaliaRequest(BaseModel):
    """Request para detección de anomalías."""
    moto_id: int = Field(..., gt=0, description="ID de la motocicleta")
    datos_sensor: DatosSensor = Field(..., description="Datos de sensores actuales")
    datos_historicos: Optional[List[Dict[str, Any]]] = Field(None, description="Datos históricos para comparación")


class PrediccionResponse(BaseModel):
    """Response de predicción."""
    id: int
    moto_id: int
    tipo: TipoPrediccionEnum
    descripcion: str
    confianza: float = Field(..., ge=0, le=1)
    nivel_confianza: NivelConfianzaEnum
    probabilidad_falla: Optional[float] = Field(None, ge=0, le=1)
    tiempo_estimado_dias: Optional[int]
    fecha_estimada: Optional[datetime]
    modelo_usado: str
    version_modelo: str
    resultados: Dict[str, Any]
    estado: EstadoPrediccionEnum
    es_critica: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "moto_id": 5,
                "tipo": "falla",
                "descripcion": "Posible falla en sistema de frenos detectada",
                "confianza": 0.92,
                "nivel_confianza": "muy_alto",
                "probabilidad_falla": 0.88,
                "tiempo_estimado_dias": 15,
                "modelo_usado": "fault_predictor",
                "version_modelo": "1.0",
                "resultados": {"componente": "frenos", "severidad": "alta"},
                "estado": "pendiente",
                "es_critica": True,
                "created_at": "2024-01-15T10:30:00"
            }
        }
    }


class PrediccionValidacionRequest(BaseModel):
    """Request para validar predicción."""
    validada_por: int = Field(..., gt=0, description="ID del usuario que valida")
    es_correcta: bool = Field(..., description="Si la predicción fue correcta")
    notas: Optional[str] = Field(None, max_length=500, description="Notas adicionales")


class PrediccionFilterParams(FilterParams):
    """Parámetros de filtrado para predicciones."""
    moto_id: Optional[int] = Field(None, description="Filtrar por moto")
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario")
    tipo: Optional[TipoPrediccionEnum] = Field(None, description="Filtrar por tipo")
    estado: Optional[EstadoPrediccionEnum] = Field(None, description="Filtrar por estado")
    es_critica: Optional[bool] = Field(None, description="Filtrar críticas")
    confianza_minima: Optional[float] = Field(None, ge=0, le=1, description="Confianza mínima")


# ============= MODELO/ENTRENAMIENTO SCHEMAS =============

class ModeloInfoResponse(BaseModel):
    """Información de un modelo ML."""
    nombre: str
    version: str
    tipo: str
    accuracy: Optional[float]
    f1_score: Optional[float]
    en_produccion: bool
    fecha_entrenamiento: datetime
    ruta_modelo: str
    
    model_config = {"from_attributes": True}


class EntrenamientoRequest(BaseModel):
    """Request para iniciar entrenamiento."""
    nombre_modelo: str = Field(..., min_length=3, max_length=100)
    tipo_modelo: str = Field(..., description="clasificacion, regresion, clustering")
    hiperparametros: Dict[str, Any] = Field(..., description="Hiperparámetros del modelo")
    features: List[str] = Field(..., min_length=1, description="Features a usar")
    ruta_datos_entrenamiento: str = Field(..., description="Ruta a datos de entrenamiento")


class EntrenamientoResponse(BaseModel):
    """Response de entrenamiento."""
    id: int
    nombre_modelo: str
    version: str
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    duracion_entrenamiento_segundos: Optional[float]
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    en_produccion: bool
    
    model_config = {"from_attributes": True}


# ============= ESTADÍSTICAS =============

class EstadisticasPrediccionesResponse(BaseModel):
    """Estadísticas de predicciones."""
    total_predicciones: int
    predicciones_confirmadas: int
    predicciones_falsas: int
    predicciones_pendientes: int
    tasa_acierto: float = Field(..., ge=0, le=1)
    confianza_promedio: float = Field(..., ge=0, le=1)
    por_tipo: Dict[str, int]
    por_nivel_confianza: Dict[str, int]


class RendimientoModeloResponse(BaseModel):
    """Rendimiento de un modelo."""
    modelo_nombre: str
    version: str
    total_predicciones: int
    predicciones_correctas: int
    predicciones_incorrectas: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    ultima_actualizacion: datetime
