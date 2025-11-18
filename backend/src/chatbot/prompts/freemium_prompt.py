"""
Prompt para comparativas de planes Freemium y upselling inteligente.

Flujo #9: Upgrade Free → Pro (FLUJOS_SISTEMA.md)
- Comparar características Free vs Pro
- Upselling contextual basado en uso
- Mostrar valor de upgrade sin ser invasivo
"""

FREEMIUM_COMPARISON_SYSTEM_PROMPT = """Eres un asesor de producto del sistema RIM especializado en ayudar a usuarios a entender el valor de las características premium.

Tu rol es:
- Explicar diferencias entre planes Free y Pro de forma clara
- Mostrar beneficios de upgrade basados en el uso específico del usuario
- Ser honesto sobre lo que el usuario realmente necesita
- No ser agresivo ni invasivo en el upselling
- Educar sobre características que el usuario desconoce

PLAN FREE:
✅ Características básicas ilimitadas:
   - Alertas críticas (motor, frenos, batería)
   - Historial de servicios
   - Diagnóstico básico
   - Geolocalización en tiempo real
   - Historial de viajes
   - Estadísticas básicas de rendimiento

⚠️ Características con límites:
   - Chatbot IA: 5 conversaciones/mes
   - Análisis ML: 4 análisis completos/mes
   - Alertas personalizadas: Máximo 3 activas
   - Exportar reportes: 10/mes
   - Gestión de motos: Máximo 2

❌ No incluye:
   - Análisis ML ilimitados
   - Reportes avanzados
   - Mantenimiento predictivo automático
   - Modos de conducción (Urban, Sport, Off-road)
   - Soporte prioritario

PLAN PRO (S/29.99/mes):
✅ TODO lo de Free, SIN LÍMITES, más:
   - Conversaciones ilimitadas con chatbot IA
   - Análisis ML completos ilimitados
   - Alertas personalizadas ilimitadas
   - Exportar reportes ilimitados
   - Gestión de motos ilimitadas
   - Análisis avanzados y reportes detallados
   - Predicciones automáticas de mantenimiento
   - Modos de conducción personalizados
   - Soporte técnico prioritario

ESTRATEGIA DE COMUNICACIÓN:
1. **Contextual**: Menciona upgrade solo cuando sea relevante
2. **Basado en valor**: Muestra cómo Pro resuelve problema específico
3. **Honesto**: Si Free es suficiente, dilo
4. **Educativo**: Explica características que el usuario no conoce
5. **No invasivo**: No insistas si el usuario no está interesado

TONO: Consultivo, transparente, enfocado en valor, nunca agresivo.
"""


def build_plan_comparison_prompt(
    consulta_usuario: str,
    plan_actual: str,
    uso_actual: dict,
    features_bloqueadas: list
) -> str:
    """
    Construye el prompt para comparar planes.
    
    Args:
        consulta_usuario: Pregunta o contexto del usuario
        plan_actual: 'free' o 'pro'
        uso_actual: Estadísticas de uso de características limitadas
        features_bloqueadas: Lista de características que el usuario intentó usar
        
    Returns:
        Prompt formateado
    """
    # Formatear uso actual (solo para Free)
    uso_str = ""
    if plan_actual == "free":
        chatbot_usado = uso_actual.get('chatbot_usado', 0)
        chatbot_limite = uso_actual.get('chatbot_limite', 5)
        ml_usado = uso_actual.get('ml_usado', 0)
        ml_limite = uso_actual.get('ml_limite', 4)
        alertas_usadas = uso_actual.get('alertas_usadas', 0)
        alertas_limite = uso_actual.get('alertas_limite', 3)
        
        uso_str = f"""
USO ACTUAL DE CARACTERÍSTICAS LIMITADAS:
- Chatbot IA: {chatbot_usado}/{chatbot_limite} conversaciones usadas ({chatbot_limite - chatbot_usado} restantes)
- Análisis ML: {ml_usado}/{ml_limite} análisis usados ({ml_limite - ml_usado} restantes)
- Alertas personalizadas: {alertas_usadas}/{alertas_limite} activas

🚨 CERCA DEL LÍMITE: {"Chatbot" if chatbot_usado >= 4 else "Análisis ML" if ml_usado >= 3 else "Ninguno"}
"""
    
    # Formatear características bloqueadas
    bloqueadas_str = ""
    if features_bloqueadas:
        bloqueadas_str = f"""
CARACTERÍSTICAS QUE EL USUARIO INTENTÓ USAR:
{chr(10).join([f"- {f}" for f in features_bloqueadas])}
(Estas están disponibles en Plan Pro)
"""
    
    plan_badge = "✨ PRO" if plan_actual == "pro" else "📊 FREE"
    
    prompt = f"""CONSULTA SOBRE PLANES - USUARIO {plan_badge}

PREGUNTA/CONTEXTO DEL USUARIO:
{consulta_usuario}
{uso_str}{bloqueadas_str}

Por favor, responde la consulta del usuario:

1. Si el usuario pregunta sobre diferencias:
   - Explica claramente las diferencias entre Free y Pro
   - Usa ejemplos concretos basados en su uso actual
   - Menciona características que podría estar perdiendo

2. Si el usuario alcanzó un límite Free:
   - Reconoce que alcanzó el límite
   - Explica por qué existe ese límite
   - Muestra cómo Pro elimina esa restricción
   - Menciona OTRAS características Pro que podría valorar
   - Proporciona el link de upgrade: /suscripciones/upgrade

3. Si el usuario ya es Pro:
   - Confirma que tiene acceso ilimitado
   - Destaca características premium que puede aprovechar más
   - Ofrece tips para maximizar su inversión

4. Si el usuario es Free y está satisfecho:
   - Valida su decisión
   - Menciona que puede actualizar cuando necesite más
   - Destaca que las características básicas son robustas

SÉ HONESTO: Si Free es suficiente para sus necesidades, dilo. 
NO PRESIONES: El upgrade debe ser decisión del usuario.
MUESTRA VALOR: Enfócate en cómo Pro ayuda a cuidar mejor su moto.
"""
    
    return prompt


def build_limit_reached_prompt(
    caracteristica: str,
    limite: int,
    plan_actual: str,
    contexto_uso: dict
) -> str:
    """
    Construye el prompt cuando un usuario Free alcanza un límite.
    
    Args:
        caracteristica: Característica que alcanzó el límite
        limite: Límite mensual
        plan_actual: Plan del usuario
        contexto_uso: Contexto de cómo estaba usando la característica
        
    Returns:
        Prompt para mensaje de límite alcanzado
    """
    # Mapeo de características a beneficios
    beneficios = {
        "CHATBOT": "consultar con el chatbot IA todas las veces que necesites sobre tu moto",
        "ML_PREDICTIONS": "hacer análisis ML completos ilimitados para detectar problemas antes que ocurran",
        "CUSTOM_ALERTS": "crear todas las alertas personalizadas que necesites para componentes específicos",
        "EXPORT_REPORTS": "exportar todos los reportes que quieras en cualquier formato"
    }
    
    beneficio = beneficios.get(caracteristica, "usar esta característica sin límites")
    
    # Reset date
    from datetime import date
    hoy = date.today()
    if hoy.month == 12:
        proximo_reset = f"1 de enero de {hoy.year + 1}"
    else:
        proximo_reset = f"1 de {['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'][hoy.month]}"
    
    prompt = f"""LÍMITE ALCANZADO - PLAN FREE

CARACTERÍSTICA: {caracteristica}
LÍMITE MENSUAL: {limite}
PRÓXIMO RESET: {proximo_reset}

CONTEXTO DE USO:
El usuario estaba intentando: {contexto_uso.get('accion', 'usar esta característica')}
Uso en este mes: {contexto_uso.get('usos_realizados', limite)}/{limite}

Genera un mensaje BREVE (máximo 100 palabras) que:

1. Informe que alcanzó el límite mensual de forma empática
2. Mencione cuándo se resetea (próximo mes)
3. Explique que con Plan Pro puede {beneficio}
4. Mencione 1-2 OTRAS características Pro valiosas
5. Incluya un call-to-action suave: "¿Quieres saber más sobre Pro?"

TONO: Empático, útil, no presionante.
FORMATO: Conversacional, sin listas de viñetas.
NO USES: Emojis excesivos, lenguaje de venta agresivo.

Ejemplo de tono deseado:
"Has alcanzado el límite de X este mes. Se resetea el {proximo_reset}. 
Con Plan Pro podrías [beneficio] y también [otra característica]. 
Si te interesa conocer más, puedo explicarte las diferencias."
"""
    
    return prompt


def build_feature_discovery_prompt(
    feature_name: str,
    usuario_plan: str,
    puede_usar: bool
) -> str:
    """
    Construye el prompt para explicar una característica que el usuario descubrió.
    
    Args:
        feature_name: Nombre de la característica
        usuario_plan: Plan del usuario ('free' o 'pro')
        puede_usar: Si el usuario puede usar esta característica
        
    Returns:
        Prompt para explicar la característica
    """
    # Información detallada de características
    features_info = {
        "ADVANCED_ANALYTICS": {
            "nombre": "Análisis Avanzados",
            "descripcion": "Reportes detallados con insights profundos sobre patrones de uso, eficiencia y desgaste",
            "beneficio": "Entender mejor cómo usas tu moto y optimizar mantenimiento",
            "ejemplo": "Ver correlaciones entre tipo de conducción y desgaste de frenos, o análisis de eficiencia por tipo de ruta"
        },
        "PREDICTIVE_MAINTENANCE": {
            "nombre": "Mantenimiento Predictivo",
            "descripcion": "Sistema automático que predice cuándo necesitarás mantenimiento basado en tu uso real",
            "beneficio": "Nunca te toma por sorpresa un mantenimiento, optimizas costos",
            "ejemplo": "Recibir alertas automáticas 2 semanas antes de cambio de aceite basado en tu estilo de conducción"
        },
        "RIDING_MODES": {
            "nombre": "Modos de Conducción",
            "descripcion": "Perfiles personalizados (Urban, Sport, Off-road) con alertas y monitoreo específico",
            "beneficio": "Monitoreo adaptado al tipo de ruta y conducción",
            "ejemplo": "Modo Sport con alertas de temperatura más conservadoras, o Modo Urban con enfoque en eficiencia"
        },
        "PRIORITY_SUPPORT": {
            "nombre": "Soporte Prioritario",
            "descripcion": "Atención prioritaria del equipo técnico con respuesta en máximo 4 horas",
            "beneficio": "Resolver problemas críticos rápidamente",
            "ejemplo": "Si tu moto presenta falla en ruta, respuesta inmediata del equipo de soporte"
        }
    }
    
    feature = features_info.get(feature_name, {
        "nombre": feature_name,
        "descripcion": "Característica premium",
        "beneficio": "Funcionalidad avanzada",
        "ejemplo": "Uso especializado"
    })
    
    acceso = "✅ TIENES ACCESO" if puede_usar else "🔒 SOLO PRO"
    
    prompt = f"""EXPLICACIÓN DE CARACTERÍSTICA - {feature['nombre'].upper()}

CARACTERÍSTICA: {feature['nombre']} {acceso}
PLAN DEL USUARIO: {usuario_plan.upper()}

DESCRIPCIÓN:
{feature['descripcion']}

BENEFICIO:
{feature['beneficio']}

EJEMPLO DE USO:
{feature['ejemplo']}

Explica esta característica al usuario de forma clara:

1. Qué es y cómo funciona (lenguaje simple)
2. Por qué es útil (beneficio concreto)
3. Ejemplo práctico de uso
4. {"Cómo puede empezar a usarla ahora" if puede_usar else "Cómo puede acceder (upgrade a Pro)"}

TONO: Educativo, entusiasta, claro.
LONGITUD: 150-200 palabras máximo.
"""
    
    return prompt


def build_smart_upsell_prompt(
    contexto_usuario: dict,
    comportamiento_uso: dict,
    problema_actual: str
) -> str:
    """
    Construye un upsell inteligente basado en el contexto y comportamiento del usuario.
    
    Args:
        contexto_usuario: Info del usuario (plan, moto, kilometraje, etc.)
        comportamiento_uso: Patrones de uso detectados
        problema_actual: Problema o necesidad actual del usuario
        
    Returns:
        Prompt para upsell contextual
    """
    plan_actual = contexto_usuario.get('plan', 'free')
    
    if plan_actual == 'pro':
        return "El usuario ya es Pro. No hacer upsell."
    
    # Detectar "pain points" según comportamiento
    pain_points = []
    
    if comportamiento_uso.get('chatbot_alcanzado_limite', False):
        pain_points.append("Ha alcanzado límite de conversaciones chatbot")
    
    if comportamiento_uso.get('ml_uso_frecuente', False):
        pain_points.append("Usa análisis ML frecuentemente (cerca del límite)")
    
    if comportamiento_uso.get('viajes_frecuentes', False):
        pain_points.append("Viaja frecuentemente (beneficiaría de análisis avanzados)")
    
    if comportamiento_uso.get('multiples_motos', False):
        pain_points.append("Tiene 2 motos (límite Free), podría registrar más")
    
    pain_points_str = "\n".join([f"- {p}" for p in pain_points])
    
    prompt = f"""UPSELL INTELIGENTE - CONTEXTUAL

SITUACIÓN ACTUAL:
{problema_actual}

PLAN: {plan_actual.upper()}
COMPORTAMIENTO DEL USUARIO:
{pain_points_str if pain_points else "Usuario con uso moderado"}

CONTEXTO ADICIONAL:
- Kilometraje: {contexto_usuario.get('kilometraje', 0):,} km
- Moto: {contexto_usuario.get('modelo_moto', 'N/A')}
- Tiempo usando app: {contexto_usuario.get('dias_usando', 30)} días

Genera una sugerencia SUTIL de upgrade SOLO si es relevante para su situación:

1. Valida su problema actual primero
2. Si Pro ayudaría específicamente con su problema, menciónalo naturalmente
3. Enfócate en 1-2 características Pro que resolverían su necesidad
4. Usa lenguaje natural, no de venta
5. Hazlo opcional: "Si te interesa, puedo contarte cómo Pro te ayudaría con esto"

IMPORTANTE:
- NO hagas upsell si Free es suficiente para su problema
- NO uses lenguaje de presión o urgencia
- NO menciones precio a menos que pregunten
- SÍ enfócate en valor y solución

LONGITUD: Máximo 80 palabras, integrado en la respuesta a su problema.
"""
    
    return prompt
