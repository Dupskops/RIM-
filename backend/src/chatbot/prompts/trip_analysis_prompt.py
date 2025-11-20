"""
Prompt para análisis y gestión de viajes de motocicleta.

Flujo #8: Gestión de Viajes (FLUJOS_SISTEMA.md)
- Análisis de patrones de conducción
- Impacto en componentes de la moto
- Estadísticas de viaje y optimización
"""

TRIP_ANALYSIS_SYSTEM_PROMPT = """Eres un analista de patrones de conducción y eficiencia del sistema RIM.

Tu rol es analizar viajes y proporcionar insights sobre:
- Estilo de conducción y su impacto en la moto
- Consumo de combustible y eficiencia
- Desgaste de componentes por tipo de ruta
- Recomendaciones para optimizar rendimiento
- Patrones de uso y mantenimiento predictivo

CAPACIDADES:
- Analizar telemetría de viajes (velocidad, RPM, aceleración, frenado)
- Evaluar impacto de ruta en componentes (urbano vs carretera)
- Calcular métricas de eficiencia (km/L, desgaste por km)
- Detectar patrones de conducción agresiva
- Sugerir mejoras en técnica de manejo

FORMATO DE ANÁLISIS DE VIAJE:
1. **Resumen del Viaje**:
   - Distancia, duración, velocidad promedio/máxima
   - Ruta (urbano, carretera, mixto)
   - Consumo de combustible

2. **Análisis de Conducción**:
   - Estilo: Agresivo, Normal, Conservador
   - Aceleraciones/frenadas bruscas
   - RPM promedio y picos
   - Temperatura motor durante el viaje

3. **Impacto en Componentes**:
   - Desgaste estimado por componente
   - Componentes más estresados
   - Recomendaciones de mantenimiento

4. **Eficiencia**:
   - Consumo real vs esperado
   - Factores que afectaron eficiencia
   - Tips para mejorar

5. **Comparativa** (Solo Pro):
   - Vs viajes previos
   - Vs promedio del usuario
   - Tendencias a lo largo del tiempo

TONO: Analítico, orientado a mejora, motivador.
"""


def build_trip_summary_prompt(
    viaje: dict,
    telemetria: dict,
    impacto_componentes: list,
    es_usuario_pro: bool
) -> str:
    """
    Construye el prompt para analizar un viaje completado.
    
    Args:
        viaje: Datos básicos del viaje
        telemetria: Métricas de telemetría del viaje
        impacto_componentes: Estimación de impacto en componentes
        es_usuario_pro: Si el usuario tiene plan Pro
        
    Returns:
        Prompt formateado
    """
    # Calcular estilo de conducción
    rpm_promedio = telemetria.get('rpm_promedio', 4000)
    aceleraciones_bruscas = telemetria.get('aceleraciones_bruscas', 0)
    frenadas_bruscas = telemetria.get('frenadas_bruscas', 0)
    
    estilo = "Normal"
    if rpm_promedio > 7000 or aceleraciones_bruscas > 10:
        estilo = "Agresivo"
    elif rpm_promedio < 3000 and aceleraciones_bruscas < 3:
        estilo = "Conservador"
    
    # Tipo de ruta
    velocidad_promedio = viaje.get('velocidad_promedio', 0)
    tipo_ruta = "Mixto"
    if velocidad_promedio < 30:
        tipo_ruta = "Urbano"
    elif velocidad_promedio > 60:
        tipo_ruta = "Carretera"
    
    # Formatear impacto componentes
    impacto_str = "\n".join([
        f"- {c.get('nombre')}: Desgaste {c.get('desgaste_estimado')}% "
        f"({'Alto' if c.get('desgaste_estimado') > 5 else 'Normal'})"
        for c in impacto_componentes[:5]  # Top 5 componentes
    ]) if impacto_componentes else "Desgaste dentro de lo normal"
    
    # Contexto del plan
    plan_context = ""
    comparativas = ""
    if es_usuario_pro:
        plan_context = "\n✨ USUARIO PRO: Incluye análisis comparativo con viajes anteriores y gráficos de tendencias."
        comparativas = """
DATOS COMPARATIVOS (vs últimos 30 días):
- Viajes similares: {stats_viajes_similares}
- Promedio velocidad: {velocidad_promedio_historica} km/h
- Consumo promedio: {consumo_promedio} L/100km
- Mejora/deterioro en eficiencia: {tendencia_eficiencia}
"""
    else:
        plan_context = "\n📊 USUARIO FREE: Análisis básico del viaje. Upgrade a Pro para comparativas históricas."
    
    prompt = f"""ANÁLISIS DE VIAJE COMPLETADO

RESUMEN:
- Distancia: {viaje.get('distancia_km', 0):.1f} km
- Duración: {viaje.get('duracion_minutos', 0)} minutos
- Velocidad promedio: {velocidad_promedio:.1f} km/h
- Velocidad máxima: {viaje.get('velocidad_maxima', 0):.1f} km/h
- Tipo de ruta: {tipo_ruta}
- Combustible consumido: {viaje.get('combustible_consumido', 0):.2f} L
{plan_context}

TELEMETRÍA:
- RPM promedio: {rpm_promedio:.0f} RPM
- RPM máximo: {telemetria.get('rpm_max', 0):.0f} RPM
- Temperatura motor promedio: {telemetria.get('temp_promedio', 0):.1f}°C
- Temperatura motor máxima: {telemetria.get('temp_max', 0):.1f}°C
- Aceleraciones bruscas: {aceleraciones_bruscas}
- Frenadas bruscas: {frenadas_bruscas}
- Estilo de conducción detectado: {estilo}

IMPACTO EN COMPONENTES:
{impacto_str}
{comparativas}

Por favor, genera un análisis completo del viaje:
1. Evaluación del viaje (distancia, tipo de ruta, condiciones)
2. Análisis del estilo de conducción (con recomendaciones si es necesario)
3. Evaluación de eficiencia de combustible
4. Impacto en componentes y desgaste esperado
5. Recomendaciones para optimizar próximos viajes
6. Si el estilo es agresivo, tips específicos para mejorarlo

Sé constructivo y enfócate en ayudar al usuario a mejorar.
"""
    
    return prompt


def build_trip_pattern_analysis_prompt(
    historial_viajes: list,
    patron_uso: dict,
    kilometraje_total: int,
    modelo_moto: str
) -> str:
    """
    Construye el prompt para analizar patrones de viajes a lo largo del tiempo.
    
    Solo disponible para usuarios Pro.
    
    Args:
        historial_viajes: Lista de viajes recientes
        patron_uso: Estadísticas agregadas de uso
        kilometraje_total: Kilometraje total acumulado
        modelo_moto: Modelo de la moto
        
    Returns:
        Prompt para análisis de patrones
    """
    # Calcular estadísticas
    total_viajes = len(historial_viajes)
    km_promedio_mes = patron_uso.get('km_promedio_mes', 1000)
    tipo_ruta_predominante = patron_uso.get('tipo_ruta_predominante', 'Mixto')
    consumo_promedio = patron_uso.get('consumo_promedio_100km', 3.5)
    
    # Top componentes más estresados
    componentes_estresados = patron_uso.get('componentes_mas_estresados', [])
    componentes_str = "\n".join([
        f"- {c.get('nombre')}: Desgaste acumulado {c.get('desgaste_total')}% "
        f"(próximo mantenimiento en {c.get('km_hasta_mantenimiento')} km)"
        for c in componentes_estresados[:5]
    ]) if componentes_estresados else "Todos los componentes dentro de lo normal"
    
    prompt = f"""ANÁLISIS DE PATRONES DE USO - {modelo_moto.upper()}

ESTADÍSTICAS GENERALES:
- Total de viajes: {total_viajes}
- Kilometraje total: {kilometraje_total:,} km
- Promedio mensual: {km_promedio_mes:,} km/mes
- Tipo de ruta predominante: {tipo_ruta_predominante}
- Consumo promedio: {consumo_promedio:.2f} L/100km

COMPONENTES MÁS ESTRESADOS:
{componentes_str}

PATRONES DETECTADOS:
- Días de mayor uso: {patron_uso.get('dias_mayor_uso', 'Fines de semana')}
- Horas de mayor uso: {patron_uso.get('horas_pico', '7-9 AM, 6-8 PM')}
- Distancia promedio por viaje: {patron_uso.get('distancia_promedio_viaje', 25):.1f} km

Por favor, genera un análisis de patrones de uso:
1. Perfil del usuario (urbano, touring, mixto)
2. Evaluación del tipo de uso vs mantenimiento requerido
3. Predicción de desgaste basado en patrones actuales
4. Recomendaciones de mantenimiento preventivo adaptadas al uso
5. Sugerencias para optimizar uso de la moto
6. Alertas sobre componentes que requieren atención por el tipo de uso

Sé específico y personalizado según los patrones detectados.
"""
    
    return prompt


def build_fuel_efficiency_analysis_prompt(
    viaje: dict,
    consumo_real: float,
    consumo_esperado: float,
    factores_impacto: dict
) -> str:
    """
    Construye el prompt para analizar eficiencia de combustible.
    
    Args:
        viaje: Datos del viaje
        consumo_real: Consumo real en L/100km
        consumo_esperado: Consumo esperado según especificaciones
        factores_impacto: Factores que afectaron el consumo
        
    Returns:
        Prompt para análisis de eficiencia
    """
    diferencia = ((consumo_real - consumo_esperado) / consumo_esperado) * 100
    
    # Formatear factores
    factores_str = "\n".join([
        f"- {factor}: {impacto.get('descripcion')} (Impacto: {impacto.get('impacto_porcentaje')}%)"
        for factor, impacto in factores_impacto.items()
    ]) if factores_impacto else "No se identificaron factores anómalos"
    
    prompt = f"""ANÁLISIS DE EFICIENCIA DE COMBUSTIBLE

VIAJE:
- Distancia: {viaje.get('distancia_km', 0):.1f} km
- Consumo real: {consumo_real:.2f} L/100km
- Consumo esperado: {consumo_esperado:.2f} L/100km
- Diferencia: {diferencia:+.1f}% {'(mejor)' if diferencia < 0 else '(peor)'} que lo esperado

FACTORES QUE AFECTARON EL CONSUMO:
{factores_str}

CONTEXTO DEL VIAJE:
- Tipo de ruta: {viaje.get('tipo_ruta', 'Desconocido')}
- Velocidad promedio: {viaje.get('velocidad_promedio', 0):.1f} km/h
- RPM promedio: {viaje.get('rpm_promedio', 0):.0f}
- Aceleraciones bruscas: {viaje.get('aceleraciones_bruscas', 0)}
- Condiciones: {viaje.get('condiciones', 'Normales')}

Analiza la eficiencia de combustible de este viaje:
1. ¿Está dentro de lo esperado o hay desviación significativa?
2. Principales factores que afectaron el consumo
3. ¿El estilo de conducción impactó negativamente?
4. Recomendaciones para mejorar eficiencia en próximos viajes
5. ¿Hay indicios de problema mecánico que afecte el consumo?

Sé específico con las recomendaciones y menciona técnicas de conducción eficiente.
"""
    
    return prompt
