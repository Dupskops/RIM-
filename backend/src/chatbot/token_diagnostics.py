"""
Herramienta de diagnóstico de tokens para el chatbot.

Permite medir y analizar cuántos tokens se están enviando al LLM
para identificar cuellos de botella y optimizar el contexto.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estima el número de tokens en un texto.
    
    Aproximación simple: ~4 caracteres por token en español.
    Para mayor precisión, usar tiktoken de OpenAI.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Número estimado de tokens
    """
    if not text:
        return 0
    
    # Aproximación: 4 caracteres por token (conservador para español)
    return len(text) // 4


def analyze_context_size(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza el tamaño del contexto y estima tokens por sección.
    
    Args:
        context: Diccionario de contexto de la moto
        
    Returns:
        Diccionario con análisis detallado
    """
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "sections": {},
        "total_estimated_tokens": 0,
        "warnings": []
    }
    
    # Analizar cada sección del contexto
    for key, value in context.items():
        if key.startswith('_'):
            continue
            
        # Convertir a string para estimar
        value_str = str(value)
        tokens = estimate_tokens(value_str)
        
        analysis["sections"][key] = {
            "size_bytes": len(value_str.encode('utf-8')),
            "size_chars": len(value_str),
            "estimated_tokens": tokens,
            "type": type(value).__name__
        }
        
        analysis["total_estimated_tokens"] += tokens
        
        # Advertencias
        if tokens > 500:
            analysis["warnings"].append(
                f"⚠️ Sección '{key}' es muy grande: ~{tokens} tokens"
            )
    
    # Advertencia general
    if analysis["total_estimated_tokens"] > 2000:
        analysis["warnings"].append(
            f"🔴 CRÍTICO: Contexto total muy grande (~{analysis['total_estimated_tokens']} tokens). "
            f"Esto puede causar timeouts."
        )
    elif analysis["total_estimated_tokens"] > 1000:
        analysis["warnings"].append(
            f"⚠️ ADVERTENCIA: Contexto grande (~{analysis['total_estimated_tokens']} tokens). "
            f"Considerar optimización."
        )
    
    return analysis


def analyze_prompts(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Analiza los prompts que se enviarán al LLM.
    
    Args:
        system_prompt: Prompt del sistema
        user_prompt: Prompt del usuario
        
    Returns:
        Diccionario con análisis
    """
    system_tokens = estimate_tokens(system_prompt)
    user_tokens = estimate_tokens(user_prompt)
    total_tokens = system_tokens + user_tokens
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "system_prompt": {
            "size_chars": len(system_prompt),
            "estimated_tokens": system_tokens,
            "percentage": (system_tokens / total_tokens * 100) if total_tokens > 0 else 0
        },
        "user_prompt": {
            "size_chars": len(user_prompt),
            "estimated_tokens": user_tokens,
            "percentage": (user_tokens / total_tokens * 100) if total_tokens > 0 else 0
        },
        "total_estimated_tokens": total_tokens,
        "warnings": []
    }
    
    # Advertencias
    if total_tokens > 3000:
        analysis["warnings"].append(
            f"🔴 CRÍTICO: Total de tokens muy alto (~{total_tokens}). "
            f"Esto causará timeouts con modelos lentos."
        )
    elif total_tokens > 2000:
        analysis["warnings"].append(
            f"⚠️ ADVERTENCIA: Total de tokens alto (~{total_tokens}). "
            f"Puede causar delays significativos."
        )
    
    if system_tokens > user_tokens * 2:
        analysis["warnings"].append(
            f"⚠️ System prompt es {system_tokens / user_tokens:.1f}x más grande que user prompt. "
            f"Considerar reducir contexto."
        )
    
    return analysis


def log_token_usage(
    conversation_id: str,
    message: str,
    context_analysis: Optional[Dict[str, Any]] = None,
    prompt_analysis: Optional[Dict[str, Any]] = None,
    response_tokens: Optional[int] = None,
    response_time_ms: Optional[int] = None
):
    """
    Registra el uso de tokens para debugging.
    
    Args:
        conversation_id: ID de la conversación
        message: Mensaje del usuario
        context_analysis: Análisis del contexto
        prompt_analysis: Análisis de prompts
        response_tokens: Tokens de la respuesta
        response_time_ms: Tiempo de respuesta en ms
    """
    log_entry = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "user_message_length": len(message),
        "user_message_tokens": estimate_tokens(message)
    }
    
    if context_analysis:
        log_entry["context_tokens"] = context_analysis.get("total_estimated_tokens", 0)
        log_entry["context_warnings"] = len(context_analysis.get("warnings", []))
    
    if prompt_analysis:
        log_entry["total_prompt_tokens"] = prompt_analysis.get("total_estimated_tokens", 0)
        log_entry["prompt_warnings"] = len(prompt_analysis.get("warnings", []))
    
    if response_tokens:
        log_entry["response_tokens"] = response_tokens
    
    if response_time_ms:
        log_entry["response_time_ms"] = response_time_ms
        log_entry["response_time_sec"] = response_time_ms / 1000
        
        # Advertencia de timeout
        if response_time_ms > 100000:  # 100 segundos
            log_entry["timeout_warning"] = "🔴 Cerca del límite de 120 seg"
    
    # Log con formato legible
    logger.info(f"[TOKEN_DIAGNOSTICS] {conversation_id}")
    logger.info(f"  User message: {log_entry['user_message_tokens']} tokens")
    
    if context_analysis:
        logger.info(f"  Context: {log_entry.get('context_tokens', 0)} tokens")
        if context_analysis.get("warnings"):
            for warning in context_analysis["warnings"]:
                logger.warning(f"    {warning}")
    
    if prompt_analysis:
        logger.info(f"  Total prompts: {log_entry.get('total_prompt_tokens', 0)} tokens")
        if prompt_analysis.get("warnings"):
            for warning in prompt_analysis["warnings"]:
                logger.warning(f"    {warning}")
    
    if response_time_ms:
        logger.info(f"  Response time: {response_time_ms / 1000:.2f} sec")
        if response_time_ms > 100000:
            logger.error(f"    {log_entry.get('timeout_warning')}")
    
    return log_entry


def get_optimization_suggestions(analysis: Dict[str, Any]) -> list[str]:
    """
    Genera sugerencias de optimización basadas en el análisis.
    
    Args:
        analysis: Análisis de contexto o prompts
        
    Returns:
        Lista de sugerencias
    """
    suggestions = []
    
    total_tokens = analysis.get("total_estimated_tokens", 0)
    
    if total_tokens > 2000:
        suggestions.append(
            "🔧 Reducir historial de mensajes previos (actualmente 2, considerar 1 o 0)"
        )
        suggestions.append(
            "🔧 Limitar lecturas de sensores a últimas 3-5 en vez de todas"
        )
        suggestions.append(
            "🔧 Resumir predicciones ML en vez de mostrar todas"
        )
    
    if "sections" in analysis:
        # Identificar secciones más grandes
        large_sections = [
            (name, data["estimated_tokens"]) 
            for name, data in analysis["sections"].items()
            if data["estimated_tokens"] > 300
        ]
        
        if large_sections:
            suggestions.append(
                f"🔧 Secciones grandes detectadas: {', '.join([s[0] for s in large_sections])}"
            )
            suggestions.append(
                "   Considerar formato más compacto o límites más estrictos"
            )
    
    return suggestions
