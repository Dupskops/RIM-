"""
Validadores de negocio para el módulo de fallas (MVP v2.3).

Proporciona validaciones usadas por los casos de uso y rutas:
- validate_falla_data: valida existencia de moto/componente antes de crear
- validate_transition_estado: valida el flujo DETECTADA -> EN_REPARACION -> RESUELTA

Las validaciones levantan ValidationException (desde src.shared.exceptions)
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shared.exceptions import ValidationException

from .models import EstadoFalla
from .schemas import FallaCreate


async def validate_falla_data(data: FallaCreate, session: AsyncSession) -> None:
	"""
	Valida datos mínimos antes de crear una falla.

	- Verifica que la moto exista
	- Verifica que el componente exista y pertenezca a la moto (si aplica)

	Lanza ValidationException si hay algún problema.
	"""
	# Importar modelos localmente para evitar ciclos de import
	from ..motos.models import Moto, Componente

	# Validar moto
	result = await session.execute(select(Moto).where(Moto.id == data.moto_id))
	moto = result.scalar_one_or_none()
	if not moto:
		raise ValidationException(f"Moto con id={data.moto_id} no existe")

	# Validar componente
	result = await session.execute(select(Componente).where(Componente.id == data.componente_id))
	componente = result.scalar_one_or_none()
	if not componente:
		raise ValidationException(f"Componente con id={data.componente_id} no existe")

	# Si el componente está ligado a una moto concreta opcionalmente validar pertenencia
	# (Si el modelo Componente tiene campo moto_id, comprobarlo sin fallar en caso de esquema distinto)
	if hasattr(componente, "moto_id"):
		if componente.moto_id is not None and componente.moto_id != data.moto_id:
			raise ValidationException("El componente no pertenece a la moto indicada")


def validate_transition_estado(estado_actual: Optional[EstadoFalla], nuevo_estado: EstadoFalla) -> None:
	"""
	Valida que la transición de estado siga el flujo establecido en v2.3.

	Flujo permitido:
		DETECTADA -> EN_REPARACION -> RESUELTA

	Args:
		estado_actual: Estado actual (puede ser Enum o string)
		nuevo_estado: Nuevo estado (Enum)

	Raises:
		ValidationException: si la transición no es permitida
	"""
	# Normalizar a valores string
	actual = None
	if estado_actual is None:
		actual = None
	elif isinstance(estado_actual, EstadoFalla):
		actual = estado_actual.value
	else:
		actual = str(estado_actual)

	nuevo = nuevo_estado.value if isinstance(nuevo_estado, EstadoFalla) else str(nuevo_estado)

	transiciones_validas = {
		EstadoFalla.DETECTADA.value: [EstadoFalla.EN_REPARACION.value],
		EstadoFalla.EN_REPARACION.value: [EstadoFalla.RESUELTA.value],
		EstadoFalla.RESUELTA.value: [],
	}

	# Si no hay estado actual (posible creación), solo permitir pasar a DETECTADA
	if actual is None:
		if nuevo != EstadoFalla.DETECTADA.value:
			raise ValidationException(f"Estado inicial inválido: {nuevo}. Debe ser '{EstadoFalla.DETECTADA.value}'")
		return

	permitidas = transiciones_validas.get(actual, [])
	if nuevo not in permitidas:
		if not permitidas:
			raise ValidationException(f"No se permiten transiciones desde el estado '{actual}'")
		raise ValidationException(f"Transición inválida: {actual} -> {nuevo}. Permitidas: {permitidas}")

