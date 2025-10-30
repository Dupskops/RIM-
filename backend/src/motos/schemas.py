from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from .models import EstadoSalud, LogicaRegla


class MotoCreateSchema(BaseModel):
    vin: str = Field(..., min_length=17, max_length=17)
    modelo: str = Field(..., max_length=100)
    ano: int = Field(..., ge=1990, le=2030)
    placa: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)
    kilometraje_actual: Decimal = Field(default=Decimal("0.0"), ge=0)
    observaciones: Optional[str] = None
    
    @field_validator("vin")
    @classmethod
    def validate_vin(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalnum():
            raise ValueError("El VIN solo puede contener caracteres alfanuméricos")
        if any(char in v for char in "IOQ"):
            raise ValueError("El VIN no puede contener las letras I, O, Q")
        return v
    
    @field_validator("placa")
    @classmethod
    def validate_placa(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().upper()
            if len(v) < 3:
                raise ValueError("La placa debe tener al menos 3 caracteres")
        return v


class MotoReadSchema(BaseModel):
    moto_id: int
    usuario_id: int
    vin: Optional[str]
    modelo: str
    ano: int
    placa: Optional[str]
    color: Optional[str]
    kilometraje_actual: Decimal
    observaciones: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MotoUpdateSchema(BaseModel):
    placa: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)
    kilometraje_actual: Optional[Decimal] = Field(None, ge=0)
    observaciones: Optional[str] = None


class MotoListResponse(BaseModel):
    items: list[MotoReadSchema]
    total: int
    page: int
    per_page: int


class EstadoActualSchema(BaseModel):
    estado_actual_id: int
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
    componente_id: int
    nombre: str
    mesh_id_3d: Optional[str]
    descripcion: Optional[str]
    
    class Config:
        from_attributes = True


class ParametroReadSchema(BaseModel):
    parametro_id: int
    nombre: str
    unidad_medida: Optional[str]
    
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
    regla_id: int
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


class HistorialLecturaReadSchema(BaseModel):
    lectura_id: int
    moto_id: int
    parametro_id: int
    parametro_nombre: Optional[str] = None
    valor: Decimal
    timestamp: datetime
    
    class Config:
        from_attributes = True
