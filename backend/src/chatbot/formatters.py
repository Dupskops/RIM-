"""
Formatters para Chatbot
Convierte datos de contexto en texto legible para el LLM.
"""
from typing import Dict, List, Any


def format_moto_context_for_llm(context: Dict[str, Any]) -> str:
    """
    Formatea el contexto de la moto en texto legible para el LLM.
    
    Args:
        context: Diccionario con datos de la moto
    
    Returns:
        String formateado para incluir en el system prompt
    """
    sections = []
    
    # 1. Información básica de la moto
    if context.get('moto_info'):
        sections.append(_format_moto_info(context['moto_info']))
    
    # 2. Estado de componentes
    if context.get('componentes'):
        sections.append(_format_componentes(context['componentes']))
    
    # 3. Fallas recientes
    if context.get('fallas_recientes'):
        sections.append(_format_fallas(context['fallas_recientes']))
    
    # 4. Mantenimientos pendientes
    if context.get('mantenimientos_pendientes'):
        sections.append(_format_mantenimientos(context['mantenimientos_pendientes']))
    
    # 5. Predicciones ML (solo Pro)
    if context.get('predicciones_ml'):
        sections.append(_format_predicciones_ml(context['predicciones_ml']))
    
    # 6. Tendencias de sensores (solo Pro)
    if context.get('tendencias_sensores'):
        sections.append(_format_tendencias_sensores(context['tendencias_sensores']))
    
    # 7. Errores de carga (si los hay)
    if context.get('_errors'):
        sections.append(_format_errors(context['_errors']))
    
    # Unir todas las secciones
    formatted_text = "\n\n".join(sections)
    
    # Agregar header
    header = "=" * 60
    header += "\nDATOS DE LA MOTO DEL USUARIO"
    header += "\n" + "=" * 60
    
    return f"{header}\n\n{formatted_text}\n\n{header}"


def _format_errors(errors: List[str]) -> str:
    """Formatea errores de carga de datos."""
    text = "⚠️ ADVERTENCIA - DATOS PARCIALES:\n"
    text += "  Algunos datos no pudieron cargarse:\n"
    for error in errors:
        text += f"    - {error}\n"
    text += "\n  IMPORTANTE: Responde con los datos disponibles y menciona que algunos datos no están disponibles temporalmente."
    return text


def _format_moto_info(moto_info: Dict[str, Any]) -> str:
    """Formatea información básica de la moto."""
    text = "📋 INFORMACIÓN DE LA MOTO:\n"
    text += f"  • Modelo: {moto_info.get('modelo', 'N/A')}\n"
    text += f"  • Marca: {moto_info.get('marca', 'N/A')}\n"
    text += f"  • Año: {moto_info.get('año', 'N/A')}\n"
    
    if moto_info.get('cilindrada'):
        text += f"  • Cilindrada: {moto_info['cilindrada']}\n"
    
    kilometraje = moto_info.get('kilometraje', 0)
    text += f"  • Kilometraje actual: {kilometraje:,.1f} km\n"
    text += f"  • Placa: {moto_info.get('placa', 'N/A')}\n"
    
    if moto_info.get('color'):
        text += f"  • Color: {moto_info['color']}\n"
    
    return text


def _format_componentes(componentes: List[Dict[str, Any]]) -> str:
    """Formatea estado de componentes."""
    if not componentes:
        return "⚙️ ESTADO DE COMPONENTES:\n  No hay datos de componentes disponibles."
    
    text = "⚙️ ESTADO DE COMPONENTES:\n"
    
    # Agrupar por estado
    por_estado = {
        'EXCELENTE': [],
        'BUENO': [],
        'ATENCION': [],
        'CRITICO': [],
        'FRIO': []
    }
    
    for comp in componentes:
        estado = comp.get('estado', 'BUENO').upper()
        if estado in por_estado:
            por_estado[estado].append(comp)
    
    # Mostrar críticos primero
    if por_estado['CRITICO']:
        text += "\n  🔴 CRÍTICOS (requieren atención inmediata):\n"
        for comp in por_estado['CRITICO']:
            text += f"    - {comp['nombre']}"
            if comp.get('ultimo_valor'):
                text += f" (valor: {comp['ultimo_valor']})"
            text += "\n"
    
    # Luego atención
    if por_estado['ATENCION']:
        text += "\n  ⚠️ REQUIEREN ATENCIÓN:\n"
        for comp in por_estado['ATENCION']:
            text += f"    - {comp['nombre']}"
            if comp.get('ultimo_valor'):
                text += f" (valor: {comp['ultimo_valor']})"
            text += "\n"
    
    # Luego buenos
    if por_estado['BUENO']:
        text += "\n  ✅ EN BUEN ESTADO:\n"
        for comp in por_estado['BUENO']:
            text += f"    - {comp['nombre']}\n"
    
    # Excelentes
    if por_estado['EXCELENTE']:
        text += "\n  ⭐ EXCELENTE ESTADO:\n"
        for comp in por_estado['EXCELENTE']:
            text += f"    - {comp['nombre']}\n"
    
    return text


def _format_fallas(fallas: List[Dict[str, Any]]) -> str:
    """Formatea fallas recientes."""
    if not fallas:
        return "✅ FALLAS RECIENTES:\n  No hay fallas activas detectadas."
    
    text = f"⚠️ FALLAS RECIENTES ({len(fallas)} activas):\n"
    
    for i, falla in enumerate(fallas, 1):
        severidad_icon = {
            'critica': '🔴',
            'alta': '🟠',
            'media': '🟡',
            'baja': '🟢'
        }.get(falla.get('severidad', 'media').lower(), '⚪')
        
        text += f"\n  {i}. {severidad_icon} {falla.get('titulo', 'Falla sin título')}\n"
        text += f"     Componente: {falla.get('componente', 'N/A')}\n"
        text += f"     Severidad: {falla.get('severidad', 'N/A').upper()}\n"
        
        if falla.get('descripcion'):
            text += f"     Descripción: {falla['descripcion']}\n"
        
        if falla.get('requiere_atencion_inmediata'):
            text += f"     ⚠️ REQUIERE ATENCIÓN INMEDIATA\n"
        
        if not falla.get('puede_conducir', True):
            text += f"     🚫 NO SE RECOMIENDA CONDUCIR\n"
    
    return text


def _format_mantenimientos(mantenimientos: List[Dict[str, Any]]) -> str:
    """Formatea mantenimientos pendientes."""
    if not mantenimientos:
        return "🔧 MANTENIMIENTOS:\n  No hay mantenimientos pendientes próximos."
    
    text = f"🔧 MANTENIMIENTOS PENDIENTES ({len(mantenimientos)}):\n"
    
    for i, mant in enumerate(mantenimientos, 1):
        tipo_icon = {
            'preventivo': '🛡️',
            'correctivo': '🔧',
            'inspeccion': '🔍'
        }.get(mant.get('tipo', 'preventivo').lower(), '🔧')
        
        text += f"\n  {i}. {tipo_icon} {mant.get('tipo', 'N/A').upper()}\n"
        
        if mant.get('descripcion'):
            text += f"     Descripción: {mant['descripcion']}\n"
        
        if mant.get('fecha_programada'):
            text += f"     Fecha programada: {mant['fecha_programada']}\n"
        
        if mant.get('kilometraje_siguiente'):
            text += f"     Kilometraje recomendado: {mant['kilometraje_siguiente']} km\n"
    
    return text


def _format_predicciones_ml(predicciones: Dict[str, Any]) -> str:
    """Formatea predicciones ML (solo Pro)."""
    componentes_pred = predicciones.get('por_componente', [])
    
    if not componentes_pred:
        return "🤖 PREDICCIONES ML:\n  No hay predicciones ML disponibles actualmente."
    
    text = f"🤖 PREDICCIONES ML ({predicciones.get('total_predicciones', 0)} predicciones):\n"
    text += "  (Análisis predictivo basado en Machine Learning)\n"
    
    for i, pred in enumerate(componentes_pred, 1):
        confianza_icon = {
            'muy_alto': '⭐⭐⭐',
            'alto': '⭐⭐',
            'medio': '⭐',
            'bajo': '⚪',
            'muy_bajo': '⚪'
        }.get(pred.get('nivel_confianza', 'medio').lower(), '⚪')
        
        text += f"\n  {i}. {pred.get('componente', 'N/A')}\n"
        text += f"     Tipo: {pred.get('tipo', 'N/A')}\n"
        text += f"     Confianza: {confianza_icon} {pred.get('nivel_confianza', 'N/A').upper()}"
        text += f" ({pred.get('confianza', 0):.1%})\n"
        
        if pred.get('probabilidad_falla'):
            text += f"     Probabilidad de falla: {pred['probabilidad_falla']:.1%}\n"
        
        if pred.get('tiempo_estimado_dias'):
            text += f"     Tiempo estimado: {pred['tiempo_estimado_dias']} días\n"
        
        if pred.get('descripcion'):
            text += f"     Detalles: {pred['descripcion']}\n"
    
    return text


def _format_tendencias_sensores(tendencias: List[Dict[str, Any]]) -> str:
    """Formatea tendencias de sensores (solo Pro)."""
    if not tendencias:
        return "📊 TENDENCIAS DE SENSORES:\n  No hay datos de tendencias disponibles."
    
    text = f"📊 TENDENCIAS DE SENSORES ({len(tendencias)} componentes monitoreados):\n"
    text += "  (Datos de los últimos 7 días)\n"
    
    for tend in tendencias:
        text += f"\n  • {tend.get('componente', 'N/A')}\n"
        text += f"    Lecturas recientes: {tend.get('total_lecturas', 0)}\n"
        
        # Mostrar últimas 3 lecturas como ejemplo
        lecturas = tend.get('lecturas_recientes', [])[:3]
        if lecturas:
            text += f"    Últimas mediciones:\n"
            for lectura in lecturas:
                valor = lectura.get('valor', {})
                timestamp = lectura.get('timestamp', 'N/A')
                text += f"      - {timestamp}: {valor}\n"
    
    return text


def format_user_plan_note(user_plan: str) -> str:
    """
    Genera una nota sobre el plan del usuario para el system prompt.
    """
    if user_plan == 'pro':
        return (
            "\n\n💎 USUARIO PRO:\n"
            "Este usuario tiene acceso completo a todas las funcionalidades premium.\n"
            "Puedes usar predicciones ML detalladas y tendencias de sensores en tus respuestas."
        )
    else:
        return (
            "\n\n📱 USUARIO FREE:\n"
            "Este usuario tiene acceso a funcionalidades básicas.\n"
            "Proporciona respuestas útiles basadas en el estado actual y fallas detectadas.\n"
            "Si es relevante, puedes mencionar que las predicciones ML detalladas están disponibles en el plan Pro."
        )
