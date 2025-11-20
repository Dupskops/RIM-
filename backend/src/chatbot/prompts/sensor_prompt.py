"""
Prompt para lectura e interpretación de sensores en tiempo real.

Flujo #3: Monitoreo en Tiempo Real (FLUJOS_SISTEMA.md)
- Interpretar lecturas actuales de sensores
- Comparar con rangos normales
- Alertar anomalías tempranas
- Explicar qué significan los valores

Basado en KTM 390 Duke 2024 con 11 componentes medibles.
"""

SENSOR_READING_SYSTEM_PROMPT = """Eres un especialista en telemetría e interpretación de sensores del sistema RIM.

Tu rol es explicar en tiempo real qué significan las lecturas de sensores y alertar sobre valores anómalos.

CAPACIDADES:
- Interpretar lecturas de sensores (temperatura, presión, voltaje, RPM, etc.)
- Comparar valores actuales con rangos normales
- Detectar tendencias preocupantes antes que sean críticas
- Explicar qué significa cada sensor en lenguaje claro
- Alertar sobre riesgos de seguridad inmediatos

COMPONENTES KTM 390 DUKE 2024 (11 total):
1. Motor (Servicio/Aceite) - Tracking de intervalos de cambio
2. Depósito de Combustible - Nivel actual (capacidad 13.4L)
3. Neumático Delantero - Presión 110/70 R17
4. Neumático Trasero - Presión 150/60 R17
5. Sistema Eléctrico - Voltaje de batería
6. Motor (Temperatura) - Temperatura operativa
7. Motor (RPM Ralentí) - Revoluciones por minuto en ralentí
8. Freno Delantero (Disco) - Espesor disco 320mm
9. Freno Delantero (Pastillas) - Espesor pastillas
10. Freno Trasero (Disco) - Espesor disco 230mm
11. Freno Trasero (Pastillas) - Espesor pastillas

ESTADOS POSIBLES:
- 🟢 EXCELENTE: Valor óptimo, sin preocupaciones
- 🟡 BUENO: Normal, dentro de rangos
- 🟠 ATENCIÓN: Requiere monitoreo, no crítico aún
- 🔴 CRÍTICO: Requiere acción inmediata, riesgo de seguridad
- 🔵 FRÍO: Motor aún no alcanzó temperatura operativa (solo temp motor)

FORMATO DE RESPUESTA:
1. **Estado Actual**: Valor + unidad + interpretación
2. **Evaluación**: Estado (EXCELENTE/BUENO/ATENCIÓN/CRÍTICO)
3. **Rango Normal**: Qué valores son esperados
4. **Qué Significa**: Explicación clara del sensor
5. **Acción Requerida**: Qué hacer ahora (si aplica)
6. **Monitoreo**: Qué vigilar en próximas lecturas

TONO: Claro, directo, tranquilizador cuando está normal, firme cuando es crítico.

PRIORIDAD: Seguridad del conductor primero. Si hay riesgo, menciónalo inmediatamente.
"""


def build_sensor_reading_prompt(
    sensor_tipo: str,
    valor_actual: float,
    unidad: str,
    estado_calculado: str,
    reglas_estado: dict,
    historial_reciente: list,
    componente_nombre: str
) -> str:
    """
    Construye el prompt para interpretar una lectura de sensor.
    
    Args:
        sensor_tipo: Tipo de sensor (temperatura, presion, voltaje, etc.)
        valor_actual: Valor actual leído
        unidad: Unidad de medida (°C, bar, V, etc.)
        estado_calculado: Estado según reglas (EXCELENTE, BUENO, ATENCIÓN, CRÍTICO, FRÍO)
        reglas_estado: Diccionario con reglas de umbral para cada estado
        historial_reciente: Últimas 5-10 lecturas
        componente_nombre: Nombre del componente (ej: "Motor (Temperatura)")
        
    Returns:
        Prompt formateado
    """
    # Formatear reglas de estado
    reglas_str = ""
    for estado, regla in reglas_estado.items():
        if regla:
            logica = regla.get('logica', 'N/A')
            valor_min = regla.get('valor_min')
            valor_max = regla.get('valor_max')
            
            if logica == 'ENTRE' and valor_min is not None and valor_max is not None:
                reglas_str += f"- {estado}: Entre {valor_min} y {valor_max} {unidad}\n"
            elif logica == 'MAYOR_QUE' and valor_max is not None:
                reglas_str += f"- {estado}: Mayor que {valor_max} {unidad}\n"
            elif logica == 'MENOR_QUE' and valor_min is not None:
                reglas_str += f"- {estado}: Menor que {valor_min} {unidad}\n"
    
    # Formatear historial
    historial_str = ""
    if historial_reciente:
        historial_str = "HISTORIAL RECIENTE (últimas lecturas):\n" + "\n".join([
            f"- {h.get('timestamp', 'N/A')}: {h.get('valor')} {unidad} ({h.get('estado')})"
            for h in historial_reciente[-5:]  # Últimas 5
        ])
    else:
        historial_str = "HISTORIAL: Primera lectura de este sensor"
    
    # Emoji según estado
    emoji = {
        "EXCELENTE": "🟢",
        "BUENO": "🟡",
        "ATENCIÓN": "🟠",
        "CRÍTICO": "🔴",
        "FRÍO": "🔵"
    }.get(estado_calculado, "⚪")
    
    # Detectar tendencia
    tendencia = "estable"
    if len(historial_reciente) >= 3:
        valores = [h.get('valor', 0) for h in historial_reciente[-3:]]
        if all(valores[i] < valores[i+1] for i in range(len(valores)-1)):
            tendencia = "creciente"
        elif all(valores[i] > valores[i+1] for i in range(len(valores)-1)):
            tendencia = "decreciente"
    
    prompt = f"""LECTURA DE SENSOR EN TIEMPO REAL

COMPONENTE: {componente_nombre}
SENSOR: {sensor_tipo}
VALOR ACTUAL: {valor_actual} {unidad}
ESTADO: {emoji} {estado_calculado}
TENDENCIA: {tendencia.upper()}

RANGOS DEFINIDOS:
{reglas_str}

{historial_str}

Por favor, interpreta esta lectura de sensor:

1. ¿Está dentro de lo normal o hay preocupación?
2. ¿Qué significa este valor específico para el componente?
3. Si el estado es ATENCIÓN o CRÍTICO, ¿qué está causando esto?
4. ¿Qué acción debe tomar el usuario AHORA?
5. ¿Qué vigilar en las próximas lecturas?
6. Si la tendencia es preocupante, ¿cuánto tiempo tiene antes que sea crítico?

IMPORTANTE:
- Si el estado es CRÍTICO, inicia tu respuesta con "⚠️ ATENCIÓN URGENTE"
- Si está en ATENCIÓN, explica por qué aún no es crítico pero requiere acción
- Si es BUENO/EXCELENTE, tranquiliza al usuario pero educa sobre el sensor
- Considera la tendencia: un valor BUENO con tendencia creciente puede ser problemático

Respuesta esperada: 100-150 palabras, clara y accionable.
"""
    
    return prompt


def build_multi_sensor_dashboard_prompt(
    lecturas_actuales: list,
    alertas_activas: list,
    modelo_moto: str,
    ultimo_analisis_ml: dict
) -> str:
    """
    Construye el prompt para interpretar el dashboard completo de sensores.
    
    Args:
        lecturas_actuales: Lista de todas las lecturas actuales (11 componentes)
        alertas_activas: Alertas activas en este momento
        modelo_moto: Modelo de la moto
        ultimo_analisis_ml: Resultado del último análisis ML (si existe)
        
    Returns:
        Prompt para resumen del dashboard
    """
    # Clasificar lecturas por estado
    criticos = [l for l in lecturas_actuales if l.get('estado') == 'CRÍTICO']
    atencion = [l for l in lecturas_actuales if l.get('estado') == 'ATENCIÓN']
    buenos = [l for l in lecturas_actuales if l.get('estado') in ['BUENO', 'EXCELENTE']]
    frios = [l for l in lecturas_actuales if l.get('estado') == 'FRÍO']
    
    # Formatear lecturas críticas
    criticos_str = "\n".join([
        f"- {l.get('componente')}: {l.get('valor')} {l.get('unidad')} "
        f"(Esperado: {l.get('rango_esperado')})"
        for l in criticos
    ]) if criticos else "✅ Ninguno"
    
    # Formatear lecturas en atención
    atencion_str = "\n".join([
        f"- {l.get('componente')}: {l.get('valor')} {l.get('unidad')}"
        for l in atencion
    ]) if atencion else "✅ Ninguno"
    
    # Formatear alertas
    alertas_str = "\n".join([
        f"- {a.get('tipo')}: {a.get('descripcion')} (Severidad: {a.get('severidad')})"
        for a in alertas_activas
    ]) if alertas_activas else "✅ No hay alertas activas"
    
    # Contexto ML si existe
    ml_context = ""
    if ultimo_analisis_ml:
        ml_context = f"""
ÚLTIMO ANÁLISIS ML:
- Fecha: {ultimo_analisis_ml.get('fecha', 'N/A')}
- Score general: {ultimo_analisis_ml.get('score_general', 0)}/100
- Predicciones detectadas: {ultimo_analisis_ml.get('num_predicciones', 0)}
"""
    
    prompt = f"""RESUMEN DEL ESTADO GENERAL - {modelo_moto.upper()}

COMPONENTES CRÍTICOS ({len(criticos)}):
{criticos_str}

COMPONENTES EN ATENCIÓN ({len(atencion)}):
{atencion_str}

COMPONENTES EN BUEN ESTADO ({len(buenos)}):
✅ {len(buenos)} componentes normales

MOTOR FRÍO:
{"🔵 Motor aún no alcanza temperatura operativa" if frios else "✅ Motor en temperatura operativa"}

ALERTAS ACTIVAS ({len(alertas_activas)}):
{alertas_str}
{ml_context}

Genera un resumen ejecutivo del estado general de la moto:

1. **Estado General**: Una frase sobre el estado global
2. **Prioridades Urgentes**: Si hay críticos o múltiples en atención
3. **Puede Conducir**: SÍ/NO con justificación clara
4. **Acciones Recomendadas**: Qué hacer ahora (priorizado)
5. **Próximo Monitoreo**: Qué componentes vigilar de cerca

FORMATO: Conciso, priorizado, accionable.
LONGITUD: 150-200 palabras máximo.

Si hay componentes CRÍTICOS, inicia con "⚠️ ATENCIÓN URGENTE".
Si todo está normal, inicia con "✅ TODO NORMAL".
"""
    
    return prompt


def build_sensor_trend_analysis_prompt(
    sensor_tipo: str,
    componente_nombre: str,
    historial_24h: list,
    valor_actual: float,
    unidad: str
) -> str:
    """
    Construye el prompt para analizar tendencias de un sensor en las últimas 24 horas.
    
    Args:
        sensor_tipo: Tipo de sensor
        componente_nombre: Nombre del componente
        historial_24h: Lecturas de las últimas 24 horas
        valor_actual: Valor actual
        unidad: Unidad de medida
        
    Returns:
        Prompt para análisis de tendencia
    """
    if not historial_24h or len(historial_24h) < 5:
        return f"""No hay suficiente historial para analizar tendencias del sensor {sensor_tipo} 
del componente {componente_nombre}. Se requieren al menos 5 lecturas en 24 horas.

Explica brevemente al usuario que estamos recopilando datos y que pronto podrá ver análisis de tendencias.
"""
    
    # Calcular estadísticas
    valores = [l.get('valor', 0) for l in historial_24h]
    valor_min = min(valores)
    valor_max = max(valores)
    valor_promedio = sum(valores) / len(valores)
    
    # Detectar patrón
    patron = "irregular"
    if valor_max - valor_min < (valor_promedio * 0.1):  # Variación < 10%
        patron = "estable"
    elif all(valores[i] <= valores[i+1] for i in range(len(valores)-1)):
        patron = "incremento constante"
    elif all(valores[i] >= valores[i+1] for i in range(len(valores)-1)):
        patron = "decremento constante"
    elif valores[-1] > valor_promedio * 1.2:
        patron = "pico reciente"
    
    # Formatear muestras
    muestras_str = "\n".join([
        f"- {l.get('timestamp')}: {l.get('valor')} {unidad}"
        for l in historial_24h[::max(1, len(historial_24h)//10)]  # Máximo 10 muestras
    ])
    
    prompt = f"""ANÁLISIS DE TENDENCIA (24 HORAS)

SENSOR: {sensor_tipo}
COMPONENTE: {componente_nombre}
LECTURAS TOTALES: {len(historial_24h)}

ESTADÍSTICAS:
- Valor actual: {valor_actual} {unidad}
- Mínimo 24h: {valor_min} {unidad}
- Máximo 24h: {valor_max} {unidad}
- Promedio 24h: {valor_promedio:.2f} {unidad}
- Rango variación: {valor_max - valor_min} {unidad}
- Patrón detectado: {patron.upper()}

MUESTRAS REPRESENTATIVAS:
{muestras_str}

Analiza la tendencia de este sensor:

1. ¿Qué patrón está mostrando en las últimas 24 horas?
2. ¿Es un comportamiento normal para este componente?
3. ¿Hay preocupación en el patrón o variación observada?
4. ¿Qué podría estar causando este patrón?
5. ¿Requiere acción o solo monitoreo?
6. ¿Cómo debería evolucionar en las próximas horas/días?

Longitud: 120-150 palabras, enfocado en insights accionables.
"""
    
    return prompt


def build_anomaly_alert_prompt(
    sensor_tipo: str,
    componente_nombre: str,
    valor_anomalo: float,
    unidad: str,
    valor_esperado: float,
    desviacion_porcentual: float,
    contexto_viaje: dict
) -> str:
    """
    Construye el prompt para alertar sobre una anomalía detectada en sensor.
    
    Args:
        sensor_tipo: Tipo de sensor
        componente_nombre: Nombre del componente
        valor_anomalo: Valor anómalo detectado
        unidad: Unidad de medida
        valor_esperado: Valor que se esperaba
        desviacion_porcentual: % de desviación
        contexto_viaje: Contexto del viaje actual (velocidad, rpm, etc.)
        
    Returns:
        Prompt para alerta de anomalía
    """
    # Clasificar severidad
    if desviacion_porcentual > 50:
        severidad = "CRÍTICA"
        emoji = "🔴"
    elif desviacion_porcentual > 30:
        severidad = "ALTA"
        emoji = "🟠"
    else:
        severidad = "MEDIA"
        emoji = "🟡"
    
    # Contexto del viaje
    en_movimiento = contexto_viaje.get('velocidad', 0) > 0
    rpm = contexto_viaje.get('rpm', 0)
    
    contexto_str = f"""
CONTEXTO ACTUAL:
- En movimiento: {'SÍ' if en_movimiento else 'NO'}
- Velocidad: {contexto_viaje.get('velocidad', 0)} km/h
- RPM: {rpm} RPM
- Temperatura motor: {contexto_viaje.get('temp_motor', 0)}°C
"""
    
    prompt = f"""{emoji} ANOMALÍA DETECTADA - SEVERIDAD {severidad}

SENSOR: {sensor_tipo}
COMPONENTE: {componente_nombre}

VALORES:
- Valor detectado: {valor_anomalo} {unidad}
- Valor esperado: {valor_esperado} {unidad}
- Desviación: {desviacion_porcentual:.1f}%
{contexto_str}

Genera una alerta clara y accionable:

1. **¿Qué sucedió?**: Descripción de la anomalía
2. **¿Es peligroso?**: Evaluación de riesgo inmediato
3. **Causa Probable**: Posibles razones (considerando contexto)
4. **Acción Inmediata**: Qué hacer AHORA
5. **Si está conduciendo**: Instrucciones específicas (detener, reducir velocidad, etc.)
6. **Seguimiento**: Qué monitorear después

CRÍTICO:
- Si severidad es CRÍTICA y está en movimiento, indica claramente si debe DETENER LA MOTO
- Si severidad es ALTA, indica si puede continuar con precauciones
- Si severidad es MEDIA, indica monitoreo requerido

LONGITUD: 100-120 palabras, directo al punto.
TONO: Firme pero no alarmista, enfocado en seguridad.
"""
    
    return prompt
