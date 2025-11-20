"""
Servicios de lógica de negocio para fallas.
MVP v2.3 - Actualizado para nuevo schema sin campos ML/diagnostic
"""
from datetime import datetime, timezone
from typing import Dict, Optional

from .models import SeveridadFalla, EstadoFalla, OrigenDeteccion


# =============================================================================
# DETERMINAR SI LA MOTO PUEDE CONDUCIRSE
# =============================================================================

def determine_puede_conducir(tipo: str, severidad: SeveridadFalla) -> bool:
    """
    Determina si la moto puede conducirse con seguridad según el tipo y severidad de falla.
    
    Args:
        tipo: Tipo de falla (string libre, ej: "sobrecalentamiento", "bateria_baja")
        severidad: Nivel de severidad de la falla
        
    Returns:
        bool: True si es seguro conducir, False si requiere detención inmediata
        
    Reglas:
        - Severidad CRITICA → NO conducir
        - Tipos críticos específicos → NO conducir (independiente de severidad)
        - Resto → puede conducir con precaución
    """
    # Fallas que NUNCA permiten conducir
    tipos_criticos = [
        "presion_aceite_baja",
        "caida_detectada", 
        "falla_frenos",
        "perdida_direccion",
        "sobrecalentamiento_extremo",
        "fuga_combustible"
    ]
    
    # Si es tipo crítico, no puede conducir
    if tipo.lower() in tipos_criticos:
        return False
    
    # Si severidad es crítica, no puede conducir
    if severidad == SeveridadFalla.CRITICA:
        return False
    
    # En otros casos puede conducir (con precaución si es severidad alta)
    return True


# =============================================================================
# GENERAR SOLUCIÓN SUGERIDA
# =============================================================================

def generate_solucion_sugerida(tipo: str, severidad: SeveridadFalla) -> str:
    """
    Genera una solución sugerida basada en el tipo y severidad de la falla.
    
    Args:
        tipo: Tipo de falla detectada
        severidad: Severidad de la falla
        
    Returns:
        str: Texto con la solución sugerida para el usuario
    """
    soluciones: Dict[str, str] = {
        # Fallas de motor
        "sobrecalentamiento": "🌡️ Detener la moto inmediatamente. Revisar nivel de refrigerante y sistema de enfriamiento. NO continuar hasta resolver.",
        "sobrecalentamiento_extremo": "🚨 PELIGRO: Apagar motor AHORA. Esperar enfriamiento completo (30 min). Llamar asistencia.",
        "presion_aceite_baja": "⚠️ Apagar motor inmediatamente. Revisar nivel de aceite. Si está bajo, NO encender hasta llenar. Puede haber fuga o falla de bomba.",
        
        # Fallas eléctricas
        "bateria_baja": "🔋 Recargar batería. Si persiste, revisar alternador y conexiones. Evitar usar accesorios eléctricos.",
        "falla_sistema_electrico": "⚡ Revisar conexiones, fusibles y alternador. Llevar a taller especializado.",
        
        # Fallas de combustible
        "nivel_combustible_critico": "⛽ Cargar combustible inmediatamente. Evitar agotar completamente el tanque.",
        "fuga_combustible": "🚨 DETENER MOTO. No encender. Revisar tanque, mangueras y carburador. Llamar asistencia.",
        
        # Fallas de frenos
        "falla_frenos": "🛑 PELIGRO: No conducir. Revisar líquido de frenos, pastillas y discos. Llevar en grúa.",
        "desgaste_pastillas_frenos": "🔧 Programar cambio de pastillas próximamente. Evitar frenadas bruscas.",
        
        # Fallas de neumáticos
        "presion_neumaticos_baja": "🏍️ Revisar y ajustar presión de neumáticos. Delantero: 2.5 bar, Trasero: 2.9 bar (KTM 390).",
        "desgaste_neumaticos": "🛞 Programar reemplazo de neumáticos. Profundidad mínima: 1.6mm.",
        
        # Fallas de suspensión
        "falla_suspension": "🔩 Revisar amortiguadores, horquilla y rodamientos. Ajustar precarga si es necesario.",
        
        # Fallas de transmisión
        "falla_cadena": "⛓️ Revisar tensión, lubricación y estado de cadena. Ajustar tensión o reemplazar si está muy desgastada.",
        "falla_embrague": "🎛️ Revisar cable de embrague y ajuste. Puede necesitar cambio de discos.",
        
        # Otras fallas
        "vibracion_anormal": "📳 Revisar balanceo de neumáticos, rodamientos y motor. Verificar montajes.",
        "ruido_anormal": "🔊 Identificar origen del ruido (motor, cadena, frenos). Revisar en taller.",
        "caida_detectada": "💥 Revisar daños estructurales, líquidos, controles y componentes críticos. Inspección completa obligatoria.",
        "perdida_direccion": "🚨 PELIGRO EXTREMO: No conducir. Revisar dirección, horquilla, rodamientos y cuadro."
    }
    
    # Buscar solución específica por tipo
    solucion = soluciones.get(tipo.lower())
    
    if solucion:
        return solucion
    
    # Solución genérica según severidad
    if severidad == SeveridadFalla.CRITICA:
        return "🚨 CRÍTICO: Detener la moto de inmediato y solicitar asistencia técnica. No continuar hasta diagnosticar el problema."
    elif severidad == SeveridadFalla.ALTA:
        return "⚠️ ALTA: Programar revisión urgente en taller. Evitar uso prolongado hasta resolver."
    elif severidad == SeveridadFalla.MEDIA:
        return "🔧 MEDIA: Agendar revisión en taller en los próximos días. Monitorear comportamiento."
    else:  # BAJA
        return "ℹ️ BAJA: Revisar en próximo mantenimiento preventivo. Continuar monitoreando."


# =============================================================================
# CALCULAR DÍAS DE RESOLUCIÓN
# =============================================================================

def calculate_dias_resolucion(fecha_deteccion: datetime, fecha_resolucion: datetime) -> int:
    """
    Calcula los días transcurridos entre detección y resolución de una falla.
    
    Args:
        fecha_deteccion: Fecha cuando se detectó la falla
        fecha_resolucion: Fecha cuando se resolvió la falla
        
    Returns:
        int: Número de días transcurridos (puede ser 0 si se resolvió el mismo día)
    """
    if not fecha_deteccion or not fecha_resolucion:
        return 0
    
    delta = fecha_resolucion - fecha_deteccion
    return max(0, delta.days)


# =============================================================================
# VALIDAR AUTO-RESOLUCIÓN
# =============================================================================

def can_auto_resolve(
    severidad: SeveridadFalla,
    origen: OrigenDeteccion,
    tipo: str
) -> bool:
    """
    Determina si una falla puede resolverse automáticamente.
    
    Criterios para auto-resolución:
    - Severidad BAJA
    - Origen SENSOR (no manual ni ML)
    - Tipos transitorios específicos
    
    Args:
        severidad: Severidad de la falla
        origen: Origen de la detección
        tipo: Tipo de falla
        
    Returns:
        bool: True si puede auto-resolverse, False en caso contrario
    """
    # Solo fallas de severidad baja pueden auto-resolverse
    if severidad != SeveridadFalla.BAJA:
        return False
    
    # Solo fallas detectadas por sensor (no manuales)
    if origen != OrigenDeteccion.SENSOR:
        return False
    
    # Tipos que pueden auto-resolverse
    tipos_auto_resolubles = [
        "vibracion_leve",
        "temperatura_alta_temporal",
        "bateria_baja_temporal",
        "presion_neumaticos_baja_leve"
    ]
    
    return tipo.lower() in tipos_auto_resolubles


# =============================================================================
# GENERAR CÓDIGO DE FALLA
# =============================================================================

def generate_falla_codigo(fecha: Optional[datetime] = None) -> str:
    """
    Genera un código único para una falla.
    
    Formato: FL-YYYYMMDD-NNN
    Ejemplo: FL-20251110-001
    
    Args:
        fecha: Fecha para el código (default: ahora)
        
    Returns:
        str: Código base (sin el número secuencial final, lo agrega el repo)
    """
    if fecha is None:
        fecha = datetime.now(timezone.utc)
    
    return f"FL-{fecha.strftime('%Y%m%d')}-"


# =============================================================================
# DETERMINAR SEVERIDAD AUTOMÁTICA
# =============================================================================

def determine_severidad_from_estado(estado_componente: str) -> SeveridadFalla:
    """
    Determina la severidad de una falla basándose en el estado del componente.
    
    Args:
        estado_componente: Estado del componente (BUENO, ATENCION, CRITICO, MANTENIMIENTO)
        
    Returns:
        SeveridadFalla: Severidad correspondiente
    """
    estado_map = {
        "CRITICO": SeveridadFalla.CRITICA,
        "ATENCION": SeveridadFalla.ALTA,
        "MANTENIMIENTO": SeveridadFalla.MEDIA,
        "BUENO": SeveridadFalla.BAJA
    }
    
    return estado_map.get(estado_componente.upper(), SeveridadFalla.MEDIA)


# =============================================================================
# CALCULAR PRIORIDAD
# =============================================================================

def calculate_prioridad(
    severidad: SeveridadFalla,
    puede_conducir: bool,
    requiere_atencion_inmediata: bool
) -> int:
    """
    Calcula un valor numérico de prioridad para ordenar fallas.
    
    Rango: 1-10 (10 = máxima prioridad)
    
    Args:
        severidad: Severidad de la falla
        puede_conducir: Si la moto puede conducirse
        requiere_atencion_inmediata: Si requiere atención urgente
        
    Returns:
        int: Valor de prioridad (1-10)
    """
    prioridad = 5  # Base
    
    # Ajustar por severidad
    if severidad == SeveridadFalla.CRITICA:
        prioridad += 4
    elif severidad == SeveridadFalla.ALTA:
        prioridad += 2
    elif severidad == SeveridadFalla.BAJA:
        prioridad -= 2
    
    # Ajustar por capacidad de conducir
    if not puede_conducir:
        prioridad += 2
    
    # Ajustar por atención inmediata
    if requiere_atencion_inmediata:
        prioridad += 1
    
    # Limitar rango
    return max(1, min(10, prioridad))
