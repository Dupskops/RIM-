"""
Prompt para recomendaciones de mantenimiento.
"""

MAINTENANCE_SYSTEM_PROMPT = """Eres un asesor especializado en mantenimiento preventivo de motocicletas del sistema RIM.

Tu rol es:
- Recomendar mantenimientos basados en datos reales
- Optimizar calendarios de mantenimiento
- Priorizar tareas según urgencia y criticidad
- Estimar costos y tiempos
- Prevenir fallas mediante mantenimiento proactivo

CAPACIDADES:
- Analizar historial de mantenimiento
- Calcular intervalos óptimos basados en uso real
- Identificar mantenimientos vencidos o próximos
- Sugerir planes de mantenimiento personalizados
- Estimar costos totales de mantenimiento

FORMATO DE RECOMENDACIÓN:
1. **Mantenimientos Urgentes**: Requieren atención inmediata
2. **Próximos Recomendados**: En los próximos 30 días
3. **Preventivos Sugeridos**: Basados en patrones de uso
4. **Estimación de Costos**: Desglose de gastos esperados
5. **Priorización**: Orden sugerido de ejecución

CRITERIOS DE PRIORIZACIÓN:
- Seguridad (máxima prioridad)
- Prevención de daños mayores
- Costo-beneficio
- Disponibilidad de tiempo del usuario
- Kilometraje y tiempo desde último servicio

TONO: Profesional, orientado a resultados, preventivo.
"""


def build_maintenance_recommendation_prompt(
    kilometraje_actual: int,
    ultimo_mantenimiento: dict,
    mantenimientos_vencidos: list,
    historial_fallas: list,
    patron_uso: dict
) -> str:
    """
    Construye el prompt para recomendaciones de mantenimiento.
    
    Args:
        kilometraje_actual: Kilometraje actual
        ultimo_mantenimiento: Datos del último mantenimiento
        mantenimientos_vencidos: Lista de mantenimientos vencidos
        historial_fallas: Fallas recurrentes
        patron_uso: Patrón de uso (km/mes, tipo de ruta, etc.)
        
    Returns:
        Prompt formateado
    """
    # Formatear último mantenimiento
    ultimo_str = f"""Último mantenimiento realizado:
- Tipo: {ultimo_mantenimiento.get('tipo', 'N/A')}
- Fecha: {ultimo_mantenimiento.get('fecha', 'N/A')}
- Kilometraje: {ultimo_mantenimiento.get('kilometraje', 0):,} km
- Hace: {kilometraje_actual - ultimo_mantenimiento.get('kilometraje', kilometraje_actual):,} km
""" if ultimo_mantenimiento else "No hay registro de mantenimientos previos"
    
    # Formatear vencidos
    vencidos_str = "\n".join([
        f"- {m.get('tipo')}: Vencido hace {m.get('dias_vencido')} días (Prioridad: {m.get('prioridad')})"
        for m in mantenimientos_vencidos
    ]) if mantenimientos_vencidos else "No hay mantenimientos vencidos"
    
    # Formatear fallas recurrentes
    fallas_str = "\n".join([
        f"- {f.get('tipo')}: {f.get('ocurrencias')} ocurrencias"
        for f in historial_fallas[:5]
    ]) if historial_fallas else "No hay fallas recurrentes"
    
    # Formatear patrón de uso
    km_mes = patron_uso.get('km_promedio_mes', 1000)
    tipo_uso = patron_uso.get('tipo_uso', 'mixto')
    
    prompt = f"""ESTADO ACTUAL DEL VEHÍCULO:
- Kilometraje actual: {kilometraje_actual:,} km
- Promedio mensual: {km_mes:,} km/mes
- Tipo de uso: {tipo_uso}

{ultimo_str}

MANTENIMIENTOS VENCIDOS:
{vencidos_str}

FALLAS RECURRENTES:
{fallas_str}

Basándote en esta información, proporciona:

1. **Plan de Mantenimiento Inmediato** (próximos 7 días)
   - Lista priorizada
   - Costo estimado total
   - Tiempo estimado de ejecución

2. **Plan Mensual** (próximos 30 días)
   - Mantenimientos programados
   - Presupuesto estimado

3. **Recomendaciones Preventivas**
   - Basadas en patrón de uso
   - Para prevenir fallas recurrentes

4. **Optimización de Costos**
   - Mantenimientos que pueden combinarse
   - Consejos para reducir gastos sin comprometer seguridad

Sé específico con fechas, costos y prioridades.
"""
    
    return prompt


def build_maintenance_schedule_prompt(
    tipo_mantenimiento: str,
    kilometraje_actual: int,
    km_promedio_mes: int
) -> str:
    """
    Construye un prompt para programar un mantenimiento específico.
    
    Args:
        tipo_mantenimiento: Tipo de mantenimiento a programar
        kilometraje_actual: Kilometraje actual
        km_promedio_mes: Promedio de km por mes
        
    Returns:
        Prompt formateado
    """
    return f"""Ayuda a programar el siguiente mantenimiento:

TIPO: {tipo_mantenimiento}
KILOMETRAJE ACTUAL: {kilometraje_actual:,} km
USO PROMEDIO: {km_promedio_mes:,} km/mes

Proporciona:
1. **Fecha Recomendada**: Cuándo debería realizarse (fecha y km)
2. **Preparación Necesaria**: Qué debe tener listo el usuario
3. **Tiempo Estimado**: Duración del servicio
4. **Costo Aproximado**: Rango de precios
5. **Qué Incluye**: Detalles del servicio
6. **Dónde Hacerlo**: Taller especializado vs servicio básico
7. **Próximo Servicio**: Cuándo será el siguiente de este tipo

Ayuda al usuario a planificar adecuadamente.
"""


def build_cost_optimization_prompt(
    mantenimientos_pendientes: list,
    presupuesto_disponible: float
) -> str:
    """
    Construye un prompt para optimizar costos de mantenimiento.
    
    Args:
        mantenimientos_pendientes: Lista de mantenimientos pendientes
        presupuesto_disponible: Presupuesto del usuario
        
    Returns:
        Prompt formateado
    """
    mantenimientos_str = "\n".join([
        f"- {m.get('tipo')}: ${m.get('costo_estimado'):,.0f} (Prioridad: {m.get('prioridad')}/5)"
        for m in mantenimientos_pendientes
    ])
    
    costo_total = sum(m.get('costo_estimado', 0) for m in mantenimientos_pendientes)
    
    return f"""SITUACIÓN:
Presupuesto disponible: ${presupuesto_disponible:,.0f}
Costo total de mantenimientos: ${costo_total:,.0f}

MANTENIMIENTOS PENDIENTES:
{mantenimientos_str}

El usuario necesita optimizar sus gastos de mantenimiento. Proporciona:

1. **Plan de Priorización**
   - Qué hacer primero y por qué
   - Qué puede esperar sin riesgo

2. **Estrategias de Ahorro**
   - Servicios que pueden combinarse
   - Alternativas más económicas
   - Qué puede hacer el usuario mismo

3. **Plan de Pagos**
   - Cómo distribuir gastos en el tiempo
   - Cuánto ahorrar mensualmente

4. **Advertencias**
   - Qué NO debe postergarse
   - Riesgos de retrasar mantenimientos

Sé realista y práctico, priorizando siempre la seguridad.
"""
