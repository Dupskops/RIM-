"""
Generador de títulos para conversaciones del chatbot.

Genera títulos cortos y precisos basados en el contenido de la conversación.
"""
from src.chatbot.models import TipoPrompt


def generate_conversation_title(
    user_message: str, 
    assistant_response: str, 
    tipo_prompt: TipoPrompt = TipoPrompt.general,
    max_length: int = 50
) -> str:
    """
    Genera un título corto y preciso basado en el mensaje del usuario y la respuesta del asistente.
    
    Analiza ambos mensajes para extraer las palabras clave más relevantes y crear un título descriptivo.
    
    Args:
        user_message: Primer mensaje del usuario
        assistant_response: Respuesta del asistente (para extraer contexto adicional)
        tipo_prompt: Tipo de prompt usado (diagnostic, maintenance, etc.)
        max_length: Longitud máxima del título (default: 50)
        
    Returns:
        Título generado corto y preciso
        
    Examples:
        >>> generate_conversation_title(
        ...     "Mi motor hace ruido extraño",
        ...     "El ruido puede ser por la cadena...",
        ...     TipoPrompt.DIAGNOSTIC
        ... )
        'Problema: motor y cadena'
        
        >>> generate_conversation_title(
        ...     "¿Cuándo cambiar el aceite?",
        ...     "Se recomienda cada 3000-5000 km...",
        ...     TipoPrompt.MAINTENANCE
        ... )
        'Mantenimiento: aceite'
    """
    # Palabras técnicas relevantes para motos
    technical_terms = {
        "motor", "freno", "aceite", "filtro", "cadena", "batería", "neumático",
        "suspensión", "embrague", "carburador", "bujía", "pastillas", "llanta",
        "refrigerante", "transmisión", "arranque", "luces", "escape", "temperatura",
        "clutch", "radiador", "disco", "amortiguador", "combustible", "gasolina"
    }
    
    # Combinar usuario y asistente para mejor contexto
    combined_text = f"{user_message} {assistant_response[:200]}".lower()
    
    # Detectar términos técnicos presentes (mantener orden de aparición)
    found_terms = []
    for term in technical_terms:
        if term in combined_text and term not in found_terms:
            found_terms.append(term)
    
    # Prefijos según tipo de prompt
    prefix_map = {
        TipoPrompt.diagnostic: "Problema",
        TipoPrompt.maintenance: "Mantenimiento",
        TipoPrompt.explanation: "Info",
        TipoPrompt.general: "Consulta"
    }
    
    prefix = prefix_map.get(tipo_prompt, "Consulta")
    
    # Construir título
    if found_terms:
        # Usar máximo 2 términos más relevantes
        main_topics = " y ".join(found_terms[:2])
        titulo = f"{prefix}: {main_topics}"
    else:
        # Extraer palabras clave del mensaje del usuario
        words = [w.strip("¿?.,!") for w in user_message.split() if len(w) > 4][:3]
        if words:
            titulo = f"{prefix}: {' '.join(words)}"
        else:
            titulo = f"{prefix} sobre moto"
    
    # Limitar longitud y limpiar
    if len(titulo) > max_length:
        titulo = titulo[:max_length - 3].rstrip() + "..."
    
    return titulo.capitalize()


def generate_simple_title(first_message: str, max_length: int = 50) -> str:
    """
    Genera un título simple basado solo en el primer mensaje del usuario.
    
    Usado como fallback cuando no hay respuesta del asistente disponible.
    
    Args:
        first_message: Primer mensaje del usuario
        max_length: Longitud máxima del título
        
    Returns:
        Título generado
    """
    # Limpiar y truncar
    titulo = first_message.strip()
    
    if len(titulo) > max_length:
        titulo = titulo[:max_length - 3].rstrip() + "..."
    
    return titulo if titulo else "Conversación sin título"
