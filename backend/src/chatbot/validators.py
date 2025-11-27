"""
Validadores de reglas de negocio para el chatbot.

Alineado con MVP v2.3 - Sistema de límites Freemium.
Funciones simplificadas. La detección de prompt se movió a ChatbotService.
"""
from typing import Optional, Any, Dict
import json

from src.chatbot.models import TipoPrompt


# ============================================
# VALIDADORES BÁSICOS
# ============================================

def validate_message_length(message: str, max_length: int = 2000) -> bool:
    """
    Valida que el mensaje no exceda la longitud máxima.
    
    Args:
        message: Mensaje a validar
        max_length: Longitud máxima permitida (default: 2000 en v2.3)
        
    Returns:
        True si es válido, False si excede el límite
    """
    return len(message.strip()) > 0 and len(message) <= max_length


def validate_conversation_id(conversation_id: str) -> bool:
    """
    Valida formato del conversation_id.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        True si el formato es válido
    """
    return len(conversation_id) > 0 and len(conversation_id) <= 100


def validate_conversation_title(titulo: str) -> bool:
    """
    Valida que el título de conversación sea válido.
    
    Args:
        titulo: Título a validar
        
    Returns:
        True si es válido
    """
    return 1 <= len(titulo.strip()) <= 200


def validate_tipo_prompt(tipo: Optional[str]) -> bool:
    """
    Valida que el tipo de prompt sea válido.
    
    Args:
        tipo: Tipo de prompt a validar
        
    Returns:
        True si es None o es un tipo válido
    """
    if tipo is None:
        return True
    
    tipos_validos = [tp.value for tp in TipoPrompt]
    return tipo in tipos_validos


def validate_context_data(context: Dict[str, Any]) -> bool:
    """
    Valida que los datos de contexto sean válidos y no excedan el tamaño.
    
    Args:
        context: Diccionario con datos de contexto
        
    Returns:
        True si el contexto es válido
    """
    try:
        context_str = json.dumps(context)
        return len(context_str) <= 50000  # Max 50KB de contexto
    except (TypeError, ValueError):
        return False


# ============================================
# VALIDADORES DE ACCESO
# ============================================

def can_delete_conversation(usuario_id: int, conversacion_usuario_id: int) -> bool:
    """
    Verifica si el usuario puede eliminar la conversación.
    
    Args:
        usuario_id: ID del usuario solicitante
        conversacion_usuario_id: ID del usuario propietario
        
    Returns:
        True si puede eliminar
    """
    return usuario_id == conversacion_usuario_id


def can_archive_conversation(usuario_id: int, conversacion_usuario_id: int) -> bool:
    """
    Verifica si el usuario puede archivar la conversación.
    
    Args:
        usuario_id: ID del usuario solicitante
        conversacion_usuario_id: ID del usuario propietario
        
    Returns:
        True si puede archivar
    """
    return usuario_id == conversacion_usuario_id


def validate_moto_access(usuario_id: int, moto_usuario_id: int) -> bool:
    """
    Verifica que el usuario tenga acceso a la moto.
    
    Args:
        usuario_id: ID del usuario
        moto_usuario_id: ID del propietario de la moto
        
    Returns:
        True si tiene acceso
    """
    return usuario_id == moto_usuario_id


# ============================================
# UTILIDADES DE ARCHIVADO
# ============================================

def should_archive_conversation(dias_inactiva: int, umbral_dias: int = 30) -> bool:
    """
    Determina si una conversación debe archivarse automáticamente.
    
    Args:
        dias_inactiva: Días desde la última actividad
        umbral_dias: Umbral en días para archivar (default: 30)
        
    Returns:
        True si debe archivarse
    """
    return dias_inactiva > umbral_dias
