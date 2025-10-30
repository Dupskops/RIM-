import re
from datetime import datetime
from decimal import Decimal


VIN_PATTERN = re.compile(r'^[A-HJ-NPR-Z0-9]{17}$')
PLACA_MIN_LENGTH = 3
ANO_MIN = 1900
ANO_MAX = datetime.now().year + 1


def validate_vin(vin: str) -> str:
    if not vin:
        raise ValueError("El VIN es obligatorio")
    vin_upper = vin.strip().upper()
    if len(vin_upper) != 17:
        raise ValueError("El VIN debe tener exactamente 17 caracteres")
    if not VIN_PATTERN.match(vin_upper):
        raise ValueError("El VIN contiene caracteres inválidos (no se permiten I, O, Q)")
    return vin_upper


def validate_placa(placa: str) -> str:
    if not placa:
        raise ValueError("La placa es obligatoria")
    placa_upper = placa.strip().upper()
    if len(placa_upper) < PLACA_MIN_LENGTH:
        raise ValueError(f"La placa debe tener al menos {PLACA_MIN_LENGTH} caracteres")
    return placa_upper


def validate_ano(ano: int) -> int:
    if ano < ANO_MIN or ano > ANO_MAX:
        raise ValueError(f"El año debe estar entre {ANO_MIN} y {ANO_MAX}")
    return ano


def validate_kilometraje(kilometraje: Decimal) -> Decimal:
    if kilometraje < 0:
        raise ValueError("El kilometraje no puede ser negativo")
    if kilometraje > Decimal("999999.9"):
        raise ValueError("El kilometraje excede el límite permitido")
    return kilometraje
