"""
Validadores para el módulo de notificaciones.
"""
from datetime import datetime, time
from typing import Optional
import re

from src.notificaciones.models import (
    PreferenciaNotificacion,
    CanalNotificacion,
    TipoNotificacion
)


def validate_titulo(titulo: str) -> None:
    """Valida el título de una notificación."""
    if not titulo or not titulo.strip():
        raise ValueError("El título no puede estar vacío")
    
    if len(titulo) < 1 or len(titulo) > 200:
        raise ValueError("El título debe tener entre 1 y 200 caracteres")


def validate_mensaje(mensaje: Optional[str]) -> None:
    """Valida el mensaje de una notificación."""
    if mensaje and len(mensaje) > 1000:
        raise ValueError("El mensaje no puede exceder los 1000 caracteres")


def validate_accion_url(url: Optional[str]) -> None:
    """Valida una URL de acción."""
    if not url:
        return
    
    # Patrón básico para URLs
    url_pattern = re.compile(
        r'^https?://'  # http:// o https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # dominio
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # puerto opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValueError("La URL de acción no es válida")


def validate_horario_no_molestar(
    hora_inicio: Optional[str],
    hora_fin: Optional[str]
) -> None:
    """Valida el horario de no molestar."""
    if not hora_inicio and not hora_fin:
        return
    
    if (hora_inicio and not hora_fin) or (not hora_inicio and hora_fin):
        raise ValueError("Debe especificar tanto hora de inicio como hora de fin")
    
    # Validar formato HH:MM
    time_pattern = re.compile(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    
    if not time_pattern.match(hora_inicio):  # type: ignore
        raise ValueError("Hora de inicio debe tener formato HH:MM")
    
    if not time_pattern.match(hora_fin):  # type: ignore
        raise ValueError("Hora de fin debe tener formato HH:MM")


def parse_time_string(time_str: str) -> time:
    """Convierte una cadena de tiempo en objeto time."""
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def esta_en_horario_no_molestar(
    preferencia: PreferenciaNotificacion,
    hora_actual: Optional[datetime] = None
) -> bool:
    """Verifica si la hora actual está en el horario de no molestar."""
    if not preferencia.no_molestar_inicio or not preferencia.no_molestar_fin:
        return False
    
    if hora_actual is None:
        hora_actual = datetime.now()
    
    hora = hora_actual.time()
    inicio = parse_time_string(preferencia.no_molestar_inicio)
    fin = parse_time_string(preferencia.no_molestar_fin)
    
    # Caso: horario dentro del mismo día
    if inicio < fin:
        return inicio <= hora < fin
    # Caso: horario que cruza medianoche
    else:
        return hora >= inicio or hora < fin


def puede_enviar_por_canal(
    preferencia: PreferenciaNotificacion,
    canal: CanalNotificacion
) -> bool:
    """Verifica si se puede enviar por un canal específico."""
    return preferencia.canal_habilitado(canal)


def puede_enviar_tipo_notificacion(
    preferencia: PreferenciaNotificacion,
    tipo: TipoNotificacion
) -> bool:
    """Verifica si se puede enviar un tipo de notificación."""
    return preferencia.tipo_notificacion_habilitado(tipo)


def puede_enviar_notificacion(
    preferencia: PreferenciaNotificacion,
    canal: CanalNotificacion,
    tipo: TipoNotificacion,
    hora_actual: Optional[datetime] = None
) -> tuple[bool, Optional[str]]:
    """
    Verifica si se puede enviar una notificación.
    
    Returns:
        tuple[bool, Optional[str]]: (puede_enviar, razon_si_no)
    """
    # Verificar horario de no molestar
    if esta_en_horario_no_molestar(preferencia, hora_actual):
        return False, "Usuario en horario de no molestar"
    
    # Verificar canal habilitado
    if not puede_enviar_por_canal(preferencia, canal):
        return False, f"Canal {canal.value} deshabilitado"
    
    # Verificar tipo de notificación habilitado
    if not puede_enviar_tipo_notificacion(preferencia, tipo):
        return False, f"Tipo de notificación {tipo.value} deshabilitado"
    
    return True, None


def validate_notificacion_data(
    titulo: str,
    mensaje: Optional[str],
    accion_url: Optional[str]
) -> None:
    """Valida todos los datos de una notificación."""
    validate_titulo(titulo)
    validate_mensaje(mensaje)
    validate_accion_url(accion_url)


def validate_referencia(
    referencia_tipo: Optional[str],
    referencia_id: Optional[int]
) -> None:
    """Valida la referencia a otra entidad."""
    if (referencia_tipo and not referencia_id) or (not referencia_tipo and referencia_id):
        raise ValueError("Debe especificar tanto tipo como ID de referencia")
    
    if referencia_tipo:
        tipos_validos = ["falla", "mantenimiento", "sensor", "conversacion"]
        if referencia_tipo not in tipos_validos:
            raise ValueError(
                f"Tipo de referencia debe ser uno de: {', '.join(tipos_validos)}"
            )
