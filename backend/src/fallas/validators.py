"""
Validadores de negocio para el módulo de fallas.
Implementa reglas de validación de dominio.
"""
from typing import Optional
from datetime import datetime

from .models import Falla
from ..shared.constants import TipoFalla, SeveridadFalla, EstadoFalla


def validate_tipo_falla(tipo: str) -> bool:
    """
    Valida que el tipo de falla sea válido.
    
    Args:
        tipo: Tipo de falla a validar
        
    Returns:
        True si es válido
        
    Raises:
        ValueError: Si el tipo no es válido
    """
    try:
        TipoFalla(tipo)
        return True
    except ValueError:
        valid_values = [t.value for t in TipoFalla]
        raise ValueError(
            f"Tipo de falla inválido: '{tipo}'. "
            f"Valores permitidos: {valid_values}"
        )


def validate_severidad(severidad: str) -> bool:
    """
    Valida que la severidad sea válida.
    
    Args:
        severidad: Severidad a validar
        
    Returns:
        True si es válido
        
    Raises:
        ValueError: Si la severidad no es válida
    """
    try:
        SeveridadFalla(severidad)
        return True
    except ValueError:
        valid_values = [s.value for s in SeveridadFalla]
        raise ValueError(
            f"Severidad inválida: '{severidad}'. "
            f"Valores permitidos: {valid_values}"
        )


def validate_estado(estado: str) -> bool:
    """
    Valida que el estado sea válido.
    
    Args:
        estado: Estado a validar
        
    Returns:
        True si es válido
        
    Raises:
        ValueError: Si el estado no es válido
    """
    try:
        EstadoFalla(estado)
        return True
    except ValueError:
        valid_values = [e.value for e in EstadoFalla]
        raise ValueError(
            f"Estado inválido: '{estado}'. "
            f"Valores permitidos: {valid_values}"
        )


def validate_transition_estado(estado_actual: str, nuevo_estado: str) -> bool:
    """
    Valida que la transición de estado sea válida.
    
    Args:
        estado_actual: Estado actual de la falla
        nuevo_estado: Nuevo estado propuesto
        
    Returns:
        True si la transición es válida
        
    Raises:
        ValueError: Si la transición no es válida
    """
    # Transiciones válidas
    transiciones_validas = {
        EstadoFalla.DETECTADA.value: [
            EstadoFalla.EN_REVISION.value,
            EstadoFalla.RESUELTA.value,
            EstadoFalla.IGNORADA.value,
        ],
        EstadoFalla.EN_REVISION.value: [
            EstadoFalla.RESUELTA.value,
            EstadoFalla.DETECTADA.value,  # Volver a detectada si se necesita más info
        ],
        EstadoFalla.RESUELTA.value: [],  # Estado final, no se puede cambiar
        EstadoFalla.IGNORADA.value: [
            EstadoFalla.DETECTADA.value,  # Reabrir si se necesita
        ],
    }
    
    estados_permitidos = transiciones_validas.get(estado_actual, [])
    
    if nuevo_estado not in estados_permitidos:
        raise ValueError(
            f"Transición inválida de '{estado_actual}' a '{nuevo_estado}'. "
            f"Estados permitidos desde '{estado_actual}': {estados_permitidos}"
        )
    
    return True


def can_update_falla(falla: Falla) -> bool:
    """
    Valida si una falla puede ser actualizada.
    
    Args:
        falla: Falla a verificar
        
    Returns:
        True si puede ser actualizada
        
    Raises:
        ValueError: Si la falla no puede ser actualizada
    """
    if falla.estado == EstadoFalla.RESUELTA.value:
        raise ValueError(
            "No se puede modificar una falla resuelta. "
            "La falla está en estado final."
        )
    
    return True


def can_delete_falla(falla: Falla) -> bool:
    """
    Valida si una falla puede ser eliminada.
    
    Args:
        falla: Falla a verificar
        
    Returns:
        True si puede ser eliminada
        
    Raises:
        ValueError: Si la falla no puede ser eliminada
    """
    if falla.estado == EstadoFalla.EN_REVISION.value:
        raise ValueError(
            "No se puede eliminar una falla en revisión. "
            "Debe resolver o cancelar la revisión primero."
        )
    
    if falla.severidad == SeveridadFalla.CRITICA.value and not falla.esta_resuelta:
        raise ValueError(
            "No se puede eliminar una falla crítica sin resolver. "
            "Debe resolverla primero."
        )
    
    return True


def validate_valores_sensor(
    valor_actual: Optional[float],
    valor_esperado: Optional[float]
) -> bool:
    """
    Valida que los valores de sensor sean coherentes.
    
    Args:
        valor_actual: Valor actual del sensor
        valor_esperado: Valor esperado del sensor
        
    Returns:
        True si son válidos
        
    Raises:
        ValueError: Si los valores no son válidos
    """
    if valor_actual is not None and valor_esperado is not None:
        # Verificar que sean números válidos
        if not isinstance(valor_actual, (int, float)):
            raise ValueError(f"Valor actual inválido: {valor_actual}")
        
        if not isinstance(valor_esperado, (int, float)):
            raise ValueError(f"Valor esperado inválido: {valor_esperado}")
    
    return True


def validate_confianza_ml(confianza: Optional[float]) -> bool:
    """
    Valida que la confianza ML esté en rango válido.
    
    Args:
        confianza: Valor de confianza (0.0 a 1.0)
        
    Returns:
        True si es válido
        
    Raises:
        ValueError: Si la confianza no está en rango
    """
    if confianza is not None:
        if not (0.0 <= confianza <= 1.0):
            raise ValueError(
                f"Confianza ML debe estar entre 0.0 y 1.0, recibido: {confianza}"
            )
    
    return True


def validate_costo(costo: Optional[float], nombre: str = "Costo") -> bool:
    """
    Valida que un costo sea válido.
    
    Args:
        costo: Valor del costo
        nombre: Nombre del campo para el mensaje de error
        
    Returns:
        True si es válido
        
    Raises:
        ValueError: Si el costo es negativo
    """
    if costo is not None:
        if costo < 0:
            raise ValueError(f"{nombre} no puede ser negativo: {costo}")
    
    return True


def validate_fechas(
    fecha_deteccion: datetime,
    fecha_diagnostico: Optional[datetime] = None,
    fecha_resolucion: Optional[datetime] = None
) -> bool:
    """
    Valida que las fechas sean coherentes.
    
    Args:
        fecha_deteccion: Fecha de detección
        fecha_diagnostico: Fecha de diagnóstico (opcional)
        fecha_resolucion: Fecha de resolución (opcional)
        
    Returns:
        True si son válidas
        
    Raises:
        ValueError: Si las fechas no son coherentes
    """
    if fecha_diagnostico:
        if fecha_diagnostico < fecha_deteccion:
            raise ValueError(
                "Fecha de diagnóstico no puede ser anterior a fecha de detección"
            )
    
    if fecha_resolucion:
        if fecha_resolucion < fecha_deteccion:
            raise ValueError(
                "Fecha de resolución no puede ser anterior a fecha de detección"
            )
        
        if fecha_diagnostico and fecha_resolucion < fecha_diagnostico:
            raise ValueError(
                "Fecha de resolución no puede ser anterior a fecha de diagnóstico"
            )
    
    return True


def is_falla_critica(severidad: str, puede_conducir: bool) -> bool:
    """
    Determina si una falla es crítica.
    
    Args:
        severidad: Severidad de la falla
        puede_conducir: Si es seguro conducir
        
    Returns:
        True si es crítica
    """
    return (
        severidad == SeveridadFalla.CRITICA.value or
        not puede_conducir
    )


def calculate_dias_resolucion(
    fecha_deteccion: datetime,
    fecha_resolucion: datetime
) -> int:
    """
    Calcula los días que tomó resolver una falla.
    
    Args:
        fecha_deteccion: Cuándo se detectó
        fecha_resolucion: Cuándo se resolvió
        
    Returns:
        Número de días
    """
    delta = fecha_resolucion - fecha_deteccion
    return max(0, delta.days)
