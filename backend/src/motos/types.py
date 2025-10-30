from typing import TypedDict, Optional


class MotoDict(TypedDict, total=False):
    moto_id: int
    usuario_id: int
    vin: str
    modelo: str
    ano: int
    placa: str
    color: Optional[str]
    kilometraje_actual: float


class ComponenteDict(TypedDict):
    componente_id: int
    nombre: str
    descripcion: Optional[str]


class ParametroDict(TypedDict):
    parametro_id: int
    componente_id: int
    nombre: str
    unidad: str


class EstadoActualDict(TypedDict):
    moto_id: int
    componente_id: int
    estado: str
    valor_actual: float
    ultima_actualizacion: str
