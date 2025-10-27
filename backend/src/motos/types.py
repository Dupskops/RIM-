"""
Tipos compartidos para el módulo `motos`.
Contienen TypedDicts simples usados por el repositorio para anotar
las formas de datos retornadas (no acoplan la capa de datos a Pydantic).
"""
from typing import TypedDict, List, Dict


class ModeloPopular(TypedDict):
    modelo: str
    count: int


class MotoStats(TypedDict):
    total_motos: int
    motos_por_año: Dict[int, int]
    kilometraje_promedio: float
    modelos_populares: List[ModeloPopular]
