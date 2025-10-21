"""
Prompt para explicaciones técnicas y educativas.
"""

EXPLANATION_SYSTEM_PROMPT = """Eres un instructor experto en mecánica de motocicletas del sistema RIM.

Tu rol es educar a los usuarios sobre:
- Funcionamiento de sistemas de la motocicleta
- Interpretación de datos de sensores
- Prevención de problemas comunes
- Buenas prácticas de mantenimiento
- Conceptos técnicos simplificados

ESTILO DE EXPLICACIÓN:
- Usa analogías simples para conceptos complejos
- Proporciona ejemplos prácticos
- Incluye visualizaciones verbales cuando sea útil
- Divide explicaciones complejas en pasos
- Usa lenguaje accesible sin sacrificar precisión técnica

FORMATO DE RESPUESTA:
1. **Concepto Principal**: Definición clara
2. **Cómo Funciona**: Explicación paso a paso
3. **Por Qué Importa**: Relevancia para el usuario
4. **Consejos Prácticos**: Recomendaciones aplicables
5. **Errores Comunes**: Qué evitar

TONO: Educativo, paciente, motivador, accesible.

ENFOQUE:
- Empodera al usuario con conocimiento
- Fomenta el mantenimiento preventivo
- Explica el "por qué" además del "qué"
- Relaciona conceptos con situaciones reales
"""


def build_explanation_prompt(
    pregunta: str,
    contexto_usuario: dict
) -> str:
    """
    Construye el prompt para explicaciones.
    
    Args:
        pregunta: Pregunta del usuario
        contexto_usuario: Contexto adicional (nivel de conocimiento, etc.)
        
    Returns:
        Prompt formateado
    """
    nivel_conocimiento = contexto_usuario.get("nivel_conocimiento", "intermedio")
    modelo_moto = contexto_usuario.get("modelo_moto", "motocicleta genérica")
    
    prompt = f"""CONTEXTO DEL USUARIO:
- Nivel de conocimiento técnico: {nivel_conocimiento}
- Motocicleta: {modelo_moto}

PREGUNTA:
{pregunta}

Proporciona una explicación clara y educativa adaptada al nivel del usuario.
"""
    
    return prompt


def build_sensor_explanation_prompt(
    sensor_tipo: str,
    valor_actual: float,
    es_anomalo: bool
) -> str:
    """
    Construye un prompt para explicar lecturas de sensores.
    
    Args:
        sensor_tipo: Tipo de sensor
        valor_actual: Valor actual del sensor
        es_anomalo: Si el valor es anómalo
        
    Returns:
        Prompt formateado
    """
    estado = "fuera de rango normal" if es_anomalo else "dentro de rango normal"
    
    return f"""Explica al usuario lo siguiente:

SENSOR: {sensor_tipo}
VALOR ACTUAL: {valor_actual}
ESTADO: {estado}

Proporciona:
1. Qué mide este sensor y por qué es importante
2. Qué significa el valor actual
3. Rango normal esperado
4. {"Posibles causas del valor anómalo y qué hacer" if es_anomalo else "Consejos para mantenerlo en rango óptimo"}

Usa un lenguaje claro y accesible.
"""


def build_maintenance_explanation_prompt(
    tipo_mantenimiento: str,
    kilometraje_actual: int
) -> str:
    """
    Construye un prompt para explicar procedimientos de mantenimiento.
    
    Args:
        tipo_mantenimiento: Tipo de mantenimiento
        kilometraje_actual: Kilometraje actual
        
    Returns:
        Prompt formateado
    """
    return f"""Explica el siguiente procedimiento de mantenimiento:

TIPO: {tipo_mantenimiento}
KILOMETRAJE ACTUAL: {kilometraje_actual:,} km

Incluye:
1. **Qué es y por qué se hace**: Propósito del mantenimiento
2. **Cuándo hacerlo**: Intervalos recomendados (km y tiempo)
3. **Consecuencias de no hacerlo**: Qué puede pasar si se ignora
4. **Señales de que es urgente**: Síntomas que indican necesidad inmediata
5. **Nivel de complejidad**: ¿Puede hacerlo el usuario o requiere taller?
6. **Costo aproximado**: Rango de precios estimado

Sé informativo y ayuda al usuario a tomar decisiones informadas.
"""
