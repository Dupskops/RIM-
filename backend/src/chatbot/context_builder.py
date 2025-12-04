"""
Context Builder para Chatbot
Construye el contexto de la moto del usuario para el LLM.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from src.motos.models import Moto, ModeloMoto, Componente, EstadoActual
from src.fallas.models import Falla
from src.mantenimiento.models import Mantenimiento
from src.ml.models import Prediccion
from src.sensores.models import Lectura
from src.suscripciones.models import Suscripcion, Plan
from src.motos.models import ReglaEstado, Parametro


async def build_moto_context(
    moto_id: int,
    user_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Construye contexto completo de la moto según el plan del usuario.
    
    Args:
        moto_id: ID de la moto
        user_id: ID del usuario (para verificar plan)
        db: Sesión de base de datos
    
    Returns:
        Diccionario con datos de la moto formateados
    """
    import logging
    logger = logging.getLogger(__name__)
    
    context = {}
    errors = []
    
    # Obtener plan del usuario
    try:
        user_plan = await get_user_plan_type(user_id, db)
        context['user_plan'] = user_plan
    except Exception as e:
        logger.warning(f"Error obteniendo plan del usuario: {e}")
        context['user_plan'] = 'free'
        errors.append(f"plan: {str(e)}")
    
    # 1. Info básica de la moto (todos)
    try:
        context['moto_info'] = await get_moto_info(moto_id, db)
    except Exception as e:
        logger.warning(f"Error obteniendo info de moto: {e}")
        context['moto_info'] = {}
        errors.append(f"moto_info: {str(e)}")
    
    # 2. Estado de componentes (todos)
    try:
        context['componentes'] = await get_componentes_estado(moto_id, db)
    except Exception as e:
        logger.warning(f"Error obteniendo componentes: {e}")
        context['componentes'] = []
        errors.append(f"componentes: {str(e)}")
    
    # 3. Fallas recientes (todos)
    try:
        context['fallas_recientes'] = await get_fallas_recientes(moto_id, db, limit=5)
    except Exception as e:
        logger.warning(f"Error obteniendo fallas: {e}")
        context['fallas_recientes'] = []
        errors.append(f"fallas: {str(e)}")
    
    # 4. Mantenimientos (todos)
    try:
        context['mantenimientos_pendientes'] = await get_mantenimientos_pendientes(moto_id, db)
    except Exception as e:
        logger.warning(f"Error obteniendo mantenimientos: {e}")
        context['mantenimientos_pendientes'] = []
        errors.append(f"mantenimientos: {str(e)}")
    
    # 4.5. Lecturas recientes de sensores (todos)
    try:
        context['lecturas_recientes'] = await get_lecturas_recientes_resumidas(moto_id, db)
    except Exception as e:
        logger.warning(f"Error obteniendo lecturas de sensores: {e}")
        context['lecturas_recientes'] = {}
        errors.append(f"lecturas_sensores: {str(e)}")
    
    # 4.6. Reglas de estado para componentes problemáticos (todos)
    try:
        context['reglas_estado'] = await get_reglas_estado_componentes(moto_id, db)
    except Exception as e:
        logger.warning(f"Error obteniendo reglas de estado: {e}")
        context['reglas_estado'] = {}
        errors.append(f"reglas_estado: {str(e)}")
    
    # 5. Datos premium (solo Pro)
    if context.get('user_plan') == 'pro':
        try:
            context['predicciones_ml'] = await get_predicciones_componentes(moto_id, db)
        except Exception as e:
            logger.warning(f"Error obteniendo predicciones ML: {e}")
            context['predicciones_ml'] = {'por_componente': [], 'total_predicciones': 0}
            errors.append(f"predicciones_ml: {str(e)}")
        
        try:
            context['tendencias_sensores'] = await get_tendencias_sensores(moto_id, db)
        except Exception as e:
            logger.warning(f"Error obteniendo tendencias de sensores: {e}")
            context['tendencias_sensores'] = []
            errors.append(f"tendencias_sensores: {str(e)}")
    
    # Agregar información sobre errores si los hubo
    if errors:
        context['_errors'] = errors
        logger.info(f"Contexto cargado con {len(errors)} errores parciales")
    
    return context


async def get_user_plan_type(user_id: int, db: AsyncSession) -> str:
    """
    Obtiene el tipo de plan del usuario.
    
    Returns:
        'free' o 'pro'
    """
    query = (
        select(Plan.nombre_plan)
        .join(Suscripcion, Suscripcion.plan_id == Plan.id)
        .where(Suscripcion.usuario_id == user_id)
        .where(Suscripcion.estado_suscripcion == 'activa')
    )
    
    result = await db.execute(query)
    plan_nombre = result.scalar_one_or_none()
    
    return plan_nombre or 'free'


async def get_moto_info(moto_id: int, db: AsyncSession) -> Dict[str, Any]:
    """Obtiene información básica de la moto."""
    query = (
        select(Moto, ModeloMoto)
        .join(ModeloMoto, Moto.modelo_moto_id == ModeloMoto.id)
        .where(Moto.id == moto_id)
    )
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        return {}
    
    moto, modelo = row
    
    return {
        'modelo': modelo.nombre,
        'marca': modelo.marca,
        'año': modelo.año,
        'cilindrada': modelo.cilindrada,
        'kilometraje': float(moto.kilometraje_actual) if moto.kilometraje_actual else 0,
        'placa': moto.placa,
        'color': moto.color
    }


async def get_componentes_estado(moto_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Obtiene el estado actual de todos los componentes de la moto."""
    query = (
        select(EstadoActual, Componente)
        .join(Componente, EstadoActual.componente_id == Componente.id)
        .where(EstadoActual.moto_id == moto_id)
        .order_by(Componente.nombre)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    componentes = []
    for estado, componente in rows:
        componentes.append({
            'nombre': componente.nombre,
            'estado': estado.estado.value if hasattr(estado.estado, 'value') else estado.estado,
            'ultimo_valor': float(estado.ultimo_valor) if estado.ultimo_valor else None,
            'ultima_actualizacion': estado.ultima_actualizacion.isoformat() if estado.ultima_actualizacion else None
        })
    
    return componentes


async def get_fallas_recientes(moto_id: int, db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    """Obtiene las fallas más recientes de la moto."""
    query = (
        select(Falla, Componente)
        .join(Componente, Falla.componente_id == Componente.id)
        .where(Falla.moto_id == moto_id)
        .where(Falla.estado != 'resuelta')  # Solo fallas activas
        .order_by(Falla.fecha_deteccion.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    fallas = []
    for falla, componente in rows:
        fallas.append({
            'componente': componente.nombre,
            'titulo': falla.titulo,
            'descripcion': falla.descripcion,
            'severidad': falla.severidad.value if hasattr(falla.severidad, 'value') else falla.severidad,
            'estado': falla.estado.value if hasattr(falla.estado, 'value') else falla.estado,
            'fecha_deteccion': falla.fecha_deteccion.isoformat() if falla.fecha_deteccion else None,
            'requiere_atencion_inmediata': falla.requiere_atencion_inmediata,
            'puede_conducir': falla.puede_conducir
        })
    
    return fallas


async def get_mantenimientos_pendientes(moto_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
    """Obtiene mantenimientos pendientes o próximos."""
    # Mantenimientos pendientes o programados para los próximos 30 días
    fecha_limite = datetime.now() + timedelta(days=30)
    
    query = (
        select(Mantenimiento)
        .where(Mantenimiento.moto_id == moto_id)
        .where(Mantenimiento.estado.in_(['pendiente', 'en_proceso']))
        .where(
            (Mantenimiento.fecha_programada.is_(None)) |
            (Mantenimiento.fecha_programada <= fecha_limite.date())
        )
        .order_by(Mantenimiento.fecha_programada.asc().nullsfirst())
    )
    
    result = await db.execute(query)
    mantenimientos_db = result.scalars().all()
    
    mantenimientos = []
    for mant in mantenimientos_db:
        mantenimientos.append({
            'tipo': mant.tipo.value if hasattr(mant.tipo, 'value') else mant.tipo,
            'estado': mant.estado.value if hasattr(mant.estado, 'value') else mant.estado,
            'descripcion': mant.descripcion,
            'fecha_programada': mant.fecha_programada.isoformat() if mant.fecha_programada else None,
            'kilometraje_actual': mant.kilometraje_actual,
            'kilometraje_siguiente': mant.kilometraje_siguiente
        })
    
    return mantenimientos


async def get_predicciones_componentes(moto_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Obtiene predicciones ML por componente (solo Pro).
    """
    # Predicciones activas de los últimos 30 días
    fecha_limite = datetime.now() - timedelta(days=30)
    
    query = (
        select(Prediccion, Componente)
        .join(Componente, Prediccion.componente_id == Componente.id, isouter=True)
        .where(Prediccion.moto_id == moto_id)
        .where(Prediccion.estado == 'pendiente')
        .where(Prediccion.created_at >= fecha_limite)
        .order_by(Prediccion.probabilidad_falla.desc().nullsfirst())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    predicciones = []
    for pred, componente in rows:
        predicciones.append({
            'componente': componente.nombre if componente else 'General',
            'tipo': pred.tipo.value if hasattr(pred.tipo, 'value') else pred.tipo,
            'descripcion': pred.descripcion,
            'confianza': float(pred.confianza) if pred.confianza else 0,
            'nivel_confianza': pred.nivel_confianza.value if hasattr(pred.nivel_confianza, 'value') else pred.nivel_confianza,
            'probabilidad_falla': float(pred.probabilidad_falla) if pred.probabilidad_falla else None,
            'tiempo_estimado_dias': pred.tiempo_estimado_dias,
            'fecha_estimada': pred.fecha_estimada.isoformat() if pred.fecha_estimada else None
        })
    
    return {
        'por_componente': predicciones,
        'total_predicciones': len(predicciones)
    }


async def get_tendencias_sensores(moto_id: int, db: AsyncSession, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene tendencias de sensores (solo Pro) - OPTIMIZADO.
    Últimas 24 horas en vez de 7 días para reducir tokens.
    """
    # Obtener últimas lecturas de las últimas 24 horas (antes: 7 días)
    fecha_limite = datetime.now() - timedelta(hours=24)
    
    query = (
        select(Lectura, Componente)
        .join(Componente, Lectura.componente_id == Componente.id)
        .where(Lectura.moto_id == moto_id)
        .where(Lectura.ts >= fecha_limite)
        .order_by(Lectura.ts.desc())
        .limit(limit * 3)  # Reducido: antes era limit * 5
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Agrupar por componente
    tendencias_por_componente = {}
    for lectura, componente in rows:
        comp_nombre = componente.nombre
        if comp_nombre not in tendencias_por_componente:
            tendencias_por_componente[comp_nombre] = []
        
        tendencias_por_componente[comp_nombre].append({
            'timestamp': lectura.ts.isoformat() if lectura.ts else None,
            'valor': lectura.valor
        })
    
    # Convertir a lista y limitar a top 3 componentes más relevantes
    tendencias = []
    for comp_nombre, lecturas in list(tendencias_por_componente.items())[:3]:  # Solo top 3
        tendencias.append({
            'componente': comp_nombre,
            'lecturas_recientes': lecturas[:limit],  # Limitar a N por componente
            'total_lecturas': len(lecturas)
        })
    
    return tendencias


async def get_lecturas_recientes_resumidas(moto_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Obtiene las últimas lecturas de sensores de forma resumida.
    Solo las últimas 3 lecturas por componente para no sobrecargar el contexto.
    """
    from datetime import datetime, timedelta
    
    # Últimas 2 horas de lecturas
    fecha_limite = datetime.now() - timedelta(hours=2)
    
    query = (
        select(Lectura, Componente, Parametro)
        .join(Componente, Lectura.componente_id == Componente.id)
        .join(Parametro, Lectura.parametro_id == Parametro.id)
        .where(Lectura.moto_id == moto_id)
        .where(Lectura.ts >= fecha_limite)
        .order_by(Lectura.ts.desc())
        .limit(30)  # Máximo 30 lecturas totales
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Agrupar por componente (solo últimas 3 por componente)
    lecturas_por_componente = {}
    for lectura, componente, parametro in rows:
        comp_nombre = componente.nombre
        if comp_nombre not in lecturas_por_componente:
            lecturas_por_componente[comp_nombre] = []
        
        # Limitar a 3 lecturas por componente
        if len(lecturas_por_componente[comp_nombre]) < 3:
            lecturas_por_componente[comp_nombre].append({
                'parametro': parametro.nombre,
                'valor': lectura.valor,
                'unidad': parametro.unidad_medida,
                'timestamp': lectura.ts.isoformat() if lectura.ts else None
            })
    
    return lecturas_por_componente


async def get_reglas_estado_componentes(moto_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Obtiene reglas de estado (umbrales) para componentes.
    Solo para componentes que tienen estado != EXCELENTE/BUENO.
    """
    # Primero obtener componentes problemáticos
    query_estado = (
        select(EstadoActual, Componente)
        .join(Componente, EstadoActual.componente_id == Componente.id)
        .where(EstadoActual.moto_id == moto_id)
        .where(EstadoActual.estado.in_(['ATENCION', 'CRITICO']))
    )
    
    result_estado = await db.execute(query_estado)
    componentes_problematicos = result_estado.all()
    
    if not componentes_problematicos:
        return {}
    
    # Obtener IDs de componentes problemáticos
    componente_ids = [comp.id for _, comp in componentes_problematicos]
    
    # Obtener reglas para esos componentes
    query_reglas = (
        select(ReglaEstado, Componente, Parametro)
        .join(Componente, ReglaEstado.componente_id == Componente.id)
        .join(Parametro, ReglaEstado.parametro_id == Parametro.id)
        .where(ReglaEstado.componente_id.in_(componente_ids))
    )
    
    result_reglas = await db.execute(query_reglas)
    reglas = result_reglas.all()
    
    # Formatear reglas
    reglas_dict = {}
    for regla, componente, parametro in reglas:
        comp_nombre = componente.nombre
        if comp_nombre not in reglas_dict:
            reglas_dict[comp_nombre] = {}
        
        reglas_dict[comp_nombre][parametro.nombre] = {
            'logica': regla.logica.value if hasattr(regla.logica, 'value') else regla.logica,
            'limite_bueno': float(regla.limite_bueno) if regla.limite_bueno else None,
            'limite_atencion': float(regla.limite_atencion) if regla.limite_atencion else None,
            'limite_critico': float(regla.limite_critico) if regla.limite_critico else None,
            'unidad': parametro.unidad_medida
        }
    
    return reglas_dict
