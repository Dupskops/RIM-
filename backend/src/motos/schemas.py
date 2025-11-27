"""
Schemas Pydantic para el módulo de motos.

Define los modelos de datos para validación y serialización de requests/responses.
Las validaciones de formato se hacen aquí con @field_validator.
Las validaciones de lógica de negocio compleja se hacen en use_cases.py.

Versión: v2.3 MVP
"""
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from .models import EstadoSalud, LogicaRegla


# ============================================
# SCHEMAS DE MODELO DE MOTO (CATÁLOGO)
# ============================================

class ModeloMotoSchema(BaseModel):
    """Schema para modelos de motos disponibles (catálogo)."""
    id: int
    nombre: str  # "KTM 390 Duke 2024"
    marca: str   # "KTM"
    año: int
    cilindrada: Optional[str] = None
    tipo_motor: Optional[str] = None
    especificaciones_tecnicas: Optional[Dict[str, Any]] = None
    activo: bool
    
    class Config:
        from_attributes = True


# ============================================
# SCHEMAS DE MOTO (INSTANCIA)
# ============================================

class MotoCreateSchema(BaseModel):
    """
    Schema para crear una nueva moto.
    
    Validaciones de formato se ejecutan automáticamente con Pydantic.
    Validaciones de negocio (unicidad VIN, existencia modelo) se hacen en el use case.
    """
    vin: str = Field(..., min_length=17, max_length=17, description="Vehicle Identification Number (17 caracteres)")
    modelo_moto_id: int = Field(..., gt=0, description="ID del modelo de moto (catálogo)")
    placa: Optional[str] = Field(None, max_length=20, description="Placa vehicular")
    color: Optional[str] = Field(None, max_length=50)
    kilometraje_actual: Decimal = Field(default=Decimal("0.0"), ge=0, le=Decimal("999999.9"))
    observaciones: Optional[str] = None
    
    @field_validator("vin")
    @classmethod
    def validate_vin(cls, v: str) -> str:
        """
        Valida formato de VIN según estándar ISO 3779.
        
        Reglas:
        - Exactamente 17 caracteres alfanuméricos
        - No permite I, O, Q (confusión visual con 1, 0)
        - Convierte a MAYÚSCULAS
        """
        v = v.strip().upper()
        if not v.isalnum():
            raise ValueError("El VIN solo puede contener caracteres alfanuméricos")
        if any(char in v for char in "IOQ"):
            raise ValueError("El VIN no puede contener las letras I, O, Q (confusión con 1, 0)")
        return v
    
    @field_validator("placa")
    @classmethod
    def validate_placa(cls, v: Optional[str]) -> Optional[str]:
        """
        Valida formato de placa vehicular.
        
        Reglas:
        - Mínimo 3 caracteres si se proporciona
        - Convierte a MAYÚSCULAS
        - Elimina espacios extra
        """
        if v:
            v = v.strip().upper()
            if len(v) < 3:
                raise ValueError("La placa debe tener al menos 3 caracteres")
        return v
    
    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza color eliminando espacios extra."""
        if v:
            v = v.strip()
        return v


class MotoReadSchema(BaseModel):
    """Schema de respuesta con datos completos de una moto."""
    id: int  # PK actualizado: moto_id → id
    usuario_id: int
    modelo_moto_id: int  # FK al catálogo de modelos
    vin: str
    placa: str
    color: Optional[str]
    kilometraje_actual: Decimal
    observaciones: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MotoUpdateSchema(BaseModel):
    """
    Schema para actualizar una moto existente.
    
    Nota: VIN y modelo_moto_id no son actualizables (datos inmutables).
    """
    placa: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)
    kilometraje_actual: Optional[Decimal] = Field(None, ge=0, le=Decimal("999999.9"))
    observaciones: Optional[str] = None
    
    @field_validator("placa")
    @classmethod
    def validate_placa(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de placa si se proporciona."""
        if v:
            v = v.strip().upper()
            if len(v) < 3:
                raise ValueError("La placa debe tener al menos 3 caracteres")
        return v
    
    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza color eliminando espacios extra."""
        if v:
            v = v.strip()
        return v


class MotoListResponse(BaseModel):
    items: list[MotoReadSchema]
    total: int
    page: int
    per_page: int


class EstadoActualSchema(BaseModel):
    id: int  # PK actualizado: estado_actual_id → id
    moto_id: int
    componente_id: int
    componente_nombre: Optional[str] = None
    ultimo_valor: Optional[Decimal] = None
    estado: EstadoSalud
    ultima_actualizacion: datetime
    
    class Config:
        from_attributes = True


class DiagnosticoGeneralSchema(BaseModel):
    moto_id: int
    estado_general: EstadoSalud
    componentes: list[EstadoActualSchema]
    ultima_actualizacion: datetime


class ComponenteReadSchema(BaseModel):
    id: int  # PK actualizado: componente_id → id
    modelo_moto_id: int
    nombre: str
    mesh_id_3d: Optional[str]
    descripcion: Optional[str]
    
    class Config:
        from_attributes = True


class ParametroReadSchema(BaseModel):
    id: int  # PK actualizado: parametro_id → id
    nombre: str
    unidad_medida: str
    
    class Config:
        from_attributes = True


class ReglaEstadoCreateSchema(BaseModel):
    componente_id: int
    parametro_id: int
    logica: LogicaRegla
    limite_bueno: Optional[Decimal] = None
    limite_atencion: Optional[Decimal] = None
    limite_critico: Optional[Decimal] = None


class ReglaEstadoReadSchema(BaseModel):
    id: int  # PK actualizado: regla_id → id
    componente_id: int
    parametro_id: int
    logica: LogicaRegla
    limite_bueno: Optional[Decimal]
    limite_atencion: Optional[Decimal]
    limite_critico: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
