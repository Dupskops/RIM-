"""
Prompt para diagnóstico de problemas de motocicleta.
"""

DIAGNOSTIC_SYSTEM_PROMPT = """Eres un asistente experto en diagnóstico de motocicletas del sistema RIM (Remote Intelligent Monitoring).

Tu rol es ayudar a diagnosticar problemas basándote en:
- Datos de sensores en tiempo real
- Historial de fallas detectadas
- Síntomas reportados por el usuario
- Patrones de uso de la motocicleta

CAPACIDADES:
- Analizar datos de sensores (temperatura, presión, voltaje, vibraciones, etc.)
- Identificar patrones de fallas comunes
- Sugerir diagnósticos precisos con nivel de confianza
- Recomendar acciones inmediatas o mantenimiento preventivo
- Evaluar criticidad de problemas detectados

FORMATO DE RESPUESTA:
1. **Diagnóstico**: Problema identificado de forma clara y concisa
2. **Severidad**: BAJA, MEDIA, ALTA o CRÍTICA
3. **Evidencia**: Datos específicos que respaldan el diagnóstico
4. **Causas Probables**: Lista de posibles causas ordenadas por probabilidad
5. **Recomendaciones**: Acciones específicas a tomar
6. **Puede Conducir**: SÍ/NO con justificación

TONO: Profesional, técnico pero comprensible, empático con el usuario.

RESTRICCIONES:
- No hagas suposiciones sin datos
- Indica nivel de confianza en diagnósticos (%)
- Si faltan datos, pregunta específicamente qué necesitas
- Prioriza la seguridad del conductor
- Menciona si se requiere asistencia profesional inmediata
"""


def build_diagnostic_prompt(
    sintomas: str,
    datos_sensores: dict,
    fallas_recientes: list,
    kilometraje: int,
    modelo_moto: str
) -> str:
    """
    Construye el prompt completo para diagnóstico.
    
    Args:
        sintomas: Descripción de síntomas del usuario
        datos_sensores: Lecturas actuales de sensores
        fallas_recientes: Lista de fallas detectadas recientemente
        kilometraje: Kilometraje actual de la moto
        modelo_moto: Modelo de la motocicleta
        
    Returns:
        Prompt formateado para el LLM
    """
    # Formatear datos de sensores
    sensores_str = "\n".join([
        f"- {sensor}: {valor} (Normal: {info.get('rango', 'N/A')})"
        for sensor, (valor, info) in datos_sensores.items()
    ])
    
    # Formatear fallas recientes
    fallas_str = "\n".join([
        f"- {falla.get('tipo')}: {falla.get('descripcion')} (Severidad: {falla.get('severidad')})"
        for falla in fallas_recientes[:5]  # Últimas 5 fallas
    ]) if fallas_recientes else "No hay fallas recientes registradas"
    
    prompt = f"""INFORMACIÓN DEL VEHÍCULO:
- Modelo: {modelo_moto}
- Kilometraje: {kilometraje:,} km

SÍNTOMAS REPORTADOS:
{sintomas}

DATOS DE SENSORES ACTUALES:
{sensores_str}

FALLAS RECIENTES:
{fallas_str}

Por favor, proporciona un diagnóstico completo siguiendo el formato especificado.
"""
    
    return prompt


def build_quick_diagnostic_prompt(sintomas: str) -> str:
    """
    Construye un prompt simplificado cuando no hay datos de sensores.
    
    Args:
        sintomas: Descripción de síntomas del usuario
        
    Returns:
        Prompt básico para diagnóstico
    """
    return f"""El usuario reporta los siguientes síntomas en su motocicleta:

{sintomas}

Basándote en tu experiencia, proporciona:
1. Posibles causas (ordenadas por probabilidad)
2. Nivel de urgencia
3. Recomendaciones inmediatas
4. Qué datos adicionales ayudarían al diagnóstico

Nota: No hay datos de sensores disponibles en este momento.
"""
