"""
Prompt para análisis ML completo de la motocicleta.

Flujo #7: Análisis ML Completo de la Moto (FLUJOS_SISTEMA.md)
- Análisis exhaustivo de TODOS los componentes usando ML
- Detección de patrones anómalos en sensores
- Predicciones de fallas inminentes
- Evaluación del estado general (score 0-100)
"""

ML_ANALYSIS_SYSTEM_PROMPT = """Eres un analista de Machine Learning especializado en mantenimiento predictivo de motocicletas del sistema RIM.

Tu rol es interpretar y comunicar resultados de análisis ML complejos de forma comprensible.

CAPACIDADES:
- Interpretar predicciones de modelos ML (clasificación, regresión, clustering)
- Explicar SHAP values y feature importance de forma simple
- Evaluar nivel de confianza de predicciones (muy_bajo a muy_alto)
- Priorizar riesgos según probabilidad e impacto
- Generar score de salud general (0-100)
- Recomendar acciones basadas en análisis predictivo

TIPOS DE ANÁLISIS:
1. **Detección de Anomalías**: Patrones inusuales en sensores
2. **Predicción de Fallas**: Probabilidad de falla en próximos 30/60/90 días
3. **Evaluación de Desgaste**: Estado actual vs esperado por kilometraje
4. **Análisis de Tendencias**: Deterioro progresivo de componentes

FORMATO DE REPORTE ML:
1. **Estado General**: Score 0-100 con interpretación
   - 90-100: Excelente
   - 70-89: Bueno
   - 50-69: Atención requerida
   - 30-49: Mantenimiento urgente
   - 0-29: Crítico

2. **Componentes Analizados**: Estado individual de cada uno (11 total)
   - Nombre del componente
   - Score individual (0-100)
   - Estado: EXCELENTE, BUENO, ATENCIÓN, CRÍTICO
   - Confianza de la predicción

3. **Predicciones Detectadas**: Solo si probabilidad > 70%
   - Tipo de falla predicha
   - Probabilidad (%)
   - Tiempo estimado hasta falla
   - Factores contribuyentes (SHAP)
   - Severidad esperada

4. **Anomalías Detectadas**: Patrones inusuales
   - Sensor/componente afectado
   - Tipo de anomalía
   - Nivel de desviación de lo normal
   - Posible causa

5. **Recomendaciones Priorizadas**: Acciones basadas en análisis
   - Urgentes (< 7 días)
   - Corto plazo (< 30 días)
   - Preventivas (30-90 días)

6. **Explicación Técnica**: Para usuarios técnicos
   - Modelo ML usado
   - Features más importantes
   - Intervalos de confianza
   - Limitaciones del análisis

TONO: Analítico, preciso, basado en datos, profesional.

RESTRICCIONES:
- Solo reporta predicciones con confianza > 70%
- Indica siempre el nivel de confianza
- Explica limitaciones del modelo
- No garantices resultados absolutos
- Recomienda validación profesional cuando sea crítico
"""


def build_ml_analysis_report_prompt(
    analysis_results: dict,
    componentes_estado: list,
    predicciones: list,
    anomalias: list,
    kilometraje: int,
    modelo_moto: str,
    es_usuario_pro: bool
) -> str:
    """
    Construye el prompt para interpretar resultados de análisis ML completo.
    
    Args:
        analysis_results: Resultados del análisis ML
        componentes_estado: Lista de 11 componentes con su estado
        predicciones: Lista de predicciones generadas (probabilidad > 70%)
        anomalias: Lista de anomalías detectadas
        kilometraje: Kilometraje actual
        modelo_moto: Modelo de la moto
        es_usuario_pro: Si el usuario tiene plan Pro
        
    Returns:
        Prompt formateado para el LLM
    """
    # Score general
    score_general = analysis_results.get('score_general', 0)
    interpretacion_score = (
        "Excelente" if score_general >= 90 else
        "Bueno" if score_general >= 70 else
        "Atención requerida" if score_general >= 50 else
        "Mantenimiento urgente" if score_general >= 30 else
        "Crítico"
    )
    
    # Formatear componentes
    componentes_str = "\n".join([
        f"- {c.get('nombre')}: {c.get('score_individual')}/100 "
        f"(Estado: {c.get('estado')}, Confianza: {c.get('confianza')}%)"
        for c in componentes_estado
    ])
    
    # Formatear predicciones
    if predicciones:
        predicciones_str = "\n".join([
            f"- {p.get('tipo_falla')}: {p.get('probabilidad')}% "
            f"(Tiempo estimado: {p.get('dias_hasta_falla')} días, Severidad: {p.get('severidad')})\n"
            f"  Factores: {', '.join(p.get('factores_shap', []))}"
            for p in predicciones
        ])
    else:
        predicciones_str = "✅ No se detectaron fallas inminentes con alta probabilidad"
    
    # Formatear anomalías
    if anomalias:
        anomalias_str = "\n".join([
            f"- {a.get('componente')}: {a.get('tipo_anomalia')} "
            f"(Desviación: {a.get('nivel_desviacion')}, Causa posible: {a.get('causa_posible')})"
            for a in anomalias
        ])
    else:
        anomalias_str = "✅ No se detectaron patrones anómalos"
    
    # Contexto del plan
    plan_context = ""
    if es_usuario_pro:
        plan_context = "\n✨ USUARIO PRO: Proporciona análisis detallado con todas las explicaciones técnicas."
    else:
        plan_context = "\n📊 USUARIO FREE: Análisis completo pero limita explicaciones técnicas avanzadas. Sugiere upgrade para análisis más frecuentes."
    
    prompt = f"""ANÁLISIS ML COMPLETO - {modelo_moto.upper()}

INFORMACIÓN GENERAL:
- Modelo: {modelo_moto}
- Kilometraje: {kilometraje:,} km
- Score de Salud General: {score_general}/100 ({interpretacion_score})
- Análisis realizado: {analysis_results.get('fecha_analisis', 'Hoy')}
{plan_context}

ESTADO DE COMPONENTES ({len(componentes_estado)} analizados):
{componentes_str}

PREDICCIONES DE FALLAS (Confianza > 70%):
{predicciones_str}

ANOMALÍAS DETECTADAS:
{anomalias_str}

DATOS TÉCNICOS DEL MODELO ML:
- Modelo usado: {analysis_results.get('modelo_tipo', 'Random Forest Classifier')}
- Features analizados: {analysis_results.get('num_features', 25)}
- Datos de entrenamiento: {analysis_results.get('training_samples', '5000+')} muestras
- Precisión del modelo: {analysis_results.get('model_accuracy', 87)}%

Por favor, genera un reporte completo siguiendo el formato especificado:
1. Resumen ejecutivo del estado general
2. Análisis detallado de cada componente crítico o en atención
3. Explicación clara de predicciones de fallas
4. Interpretación de anomalías detectadas
5. Recomendaciones priorizadas por urgencia
6. Próximos pasos sugeridos

Usa lenguaje claro pero técnicamente preciso. El usuario necesita entender qué hacer con esta información.
"""
    
    return prompt


def build_quick_ml_summary_prompt(
    score_general: int,
    num_componentes_criticos: int,
    num_predicciones: int,
    modelo_moto: str
) -> str:
    """
    Construye un prompt simplificado para resumen rápido de ML.
    
    Útil para notificaciones o cuando el usuario pide un resumen ejecutivo.
    
    Args:
        score_general: Score de salud 0-100
        num_componentes_criticos: Cantidad de componentes en estado crítico/atención
        num_predicciones: Cantidad de predicciones de falla detectadas
        modelo_moto: Modelo de la moto
        
    Returns:
        Prompt simplificado
    """
    interpretacion = (
        "Excelente" if score_general >= 90 else
        "Bueno" if score_general >= 70 else
        "Atención" if score_general >= 50 else
        "Urgente" if score_general >= 30 else
        "Crítico"
    )
    
    prompt = f"""Genera un resumen ejecutivo breve (máximo 150 palabras) del análisis ML de esta {modelo_moto}:

Estado General: {score_general}/100 ({interpretacion})
Componentes requieren atención: {num_componentes_criticos}
Fallas predichas: {num_predicciones}

El resumen debe incluir:
1. Una frase sobre el estado general
2. Mención de componentes críticos (si hay)
3. Acción más urgente recomendada
4. Tono: Claro y directo

Formato: Solo texto, sin viñetas ni títulos.
"""
    
    return prompt


def build_component_specific_analysis_prompt(
    componente: dict,
    prediccion_ml: dict,
    historial_lecturas: list,
    reglas_estado: dict
) -> str:
    """
    Construye un prompt para análisis profundo de un componente específico.
    
    Args:
        componente: Datos del componente (nombre, estado actual, score)
        prediccion_ml: Predicción ML para este componente
        historial_lecturas: Lecturas históricas del sensor asociado
        reglas_estado: Reglas de umbrales para este componente
        
    Returns:
        Prompt para análisis específico
    """
    nombre = componente.get('nombre')
    estado_actual = componente.get('estado')
    score = componente.get('score_individual', 0)
    
    # Formatear historial (últimas 10 lecturas)
    historial_str = "\n".join([
        f"- {h.get('timestamp')}: {h.get('valor')} {h.get('unidad')} (Estado: {h.get('estado_calculado')})"
        for h in historial_lecturas[-10:]
    ]) if historial_lecturas else "No hay historial disponible"
    
    # Formatear reglas
    reglas_str = ""
    for estado, regla in reglas_estado.items():
        reglas_str += f"- {estado}: {regla.get('descripcion')}\n"
    
    # Predicción
    prediccion_str = "No hay predicción de falla para este componente"
    if prediccion_ml:
        prediccion_str = f"""Predicción ML detectada:
- Tipo: {prediccion_ml.get('tipo_falla')}
- Probabilidad: {prediccion_ml.get('probabilidad')}%
- Tiempo estimado: {prediccion_ml.get('dias_hasta_falla')} días
- Factores contribuyentes: {', '.join(prediccion_ml.get('factores_shap', []))}
"""
    
    prompt = f"""ANÁLISIS PROFUNDO DE COMPONENTE

COMPONENTE: {nombre}
Estado Actual: {estado_actual}
Score ML: {score}/100

HISTORIAL DE LECTURAS (últimas 10):
{historial_str}

REGLAS DE ESTADO DEFINIDAS:
{reglas_str}

{prediccion_str}

Proporciona un análisis detallado de este componente:
1. Interpretación del estado actual
2. Tendencia observada en el historial
3. Evaluación de la predicción ML (si existe)
4. Factores de riesgo identificados
5. Recomendaciones específicas para este componente
6. Cómo monitorear su evolución

Sé específico y técnico, pero comprensible.
"""
    
    return prompt
