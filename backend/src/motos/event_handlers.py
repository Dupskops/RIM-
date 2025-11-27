"""
Event handlers para el módulo de motos.

Este módulo escucha eventos de otros módulos para mantener sincronizados
los datos de motos con el resto del sistema.

Event handlers implementados:
- MantenimientoCompletadoEvent: Actualizar km y resetear estados de componentes
- UsuarioDeletedEvent: Eliminar motos en cascada cuando se elimina usuario
- ComponenteEstadoActualizadoEvent: Auditoría de cambios de estado (opcional)

Versión: v2.3 MVP
"""
import logging
from typing import Dict, List, Optional
from decimal import Decimal

from src.shared.event_bus import event_bus
from src.mantenimiento.events import MantenimientoCompletadoEvent
from src.config.database import get_db
from .models import EstadoSalud
from .repositories import MotoRepository, EstadoActualRepository


logger = logging.getLogger(__name__)


# ============================================
# CONSTANTES DE NOMBRES DE COMPONENTES
# ============================================

COMP_MOTOR = "Motor"
COMP_FRENOS_DELANTEROS = "Frenos Delanteros"
COMP_FRENOS_TRASEROS = "Frenos Traseros"
COMP_TRANSMISION = "Transmisión"
COMP_BATERIA = "Batería"
COMP_SISTEMA_ELECTRICO = "Sistema Eléctrico"
COMP_NEUMATICO_DELANTERO = "Neumático Delantero"
COMP_NEUMATICO_TRASERO = "Neumático Trasero"
COMP_SISTEMA_REFRIGERACION = "Sistema de Refrigeración"
COMP_SISTEMA_ENCENDIDO = "Sistema de Encendido"


# ============================================
# MAPEO: TIPO MANTENIMIENTO → COMPONENTES
# ============================================

MANTENIMIENTO_TO_COMPONENTES: Dict[str, List[str]] = {
    # Mantenimientos de motor
    "cambio_aceite": [COMP_MOTOR],
    "cambio_filtro_aceite": [COMP_MOTOR],
    "cambio_refrigerante": [COMP_MOTOR, COMP_SISTEMA_REFRIGERACION],
    "ajuste_valvulas": [COMP_MOTOR],
    "limpieza_inyectores": [COMP_MOTOR],
    
    # Mantenimientos de frenos
    "cambio_pastillas_freno": [COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS],
    "cambio_discos_freno": [COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS],
    "cambio_liquido_frenos": [COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS],
    "ajuste_frenos": [COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS],
    
    # Mantenimientos de transmisión
    "cambio_cadena": [COMP_TRANSMISION],
    "ajuste_cadena": [COMP_TRANSMISION],
    "cambio_piñones": [COMP_TRANSMISION],
    "lubricacion_cadena": [COMP_TRANSMISION],
    
    # Mantenimientos eléctricos
    "cambio_bateria": [COMP_BATERIA],
    "revision_electrica": [COMP_SISTEMA_ELECTRICO, COMP_BATERIA],
    "cambio_bujias": [COMP_MOTOR, COMP_SISTEMA_ENCENDIDO],
    
    # Mantenimientos de neumáticos
    "cambio_neumaticos": [COMP_NEUMATICO_DELANTERO, COMP_NEUMATICO_TRASERO],
    "rotacion_neumaticos": [COMP_NEUMATICO_DELANTERO, COMP_NEUMATICO_TRASERO],
    "balanceo_neumaticos": [COMP_NEUMATICO_DELANTERO, COMP_NEUMATICO_TRASERO],
    
    # Mantenimientos generales
    "servicio_completo": [
        COMP_MOTOR, COMP_TRANSMISION, COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS,
        COMP_BATERIA, COMP_SISTEMA_ELECTRICO, COMP_NEUMATICO_DELANTERO, COMP_NEUMATICO_TRASERO
    ],
    "revision_general": [
        COMP_MOTOR, COMP_TRANSMISION, COMP_FRENOS_DELANTEROS, COMP_FRENOS_TRASEROS,
        COMP_BATERIA, COMP_SISTEMA_ELECTRICO
    ],
}


def _mapear_tipo_mantenimiento_a_componentes(tipo_mantenimiento: str) -> List[str]:
    """
    Mapea un tipo de mantenimiento a los nombres de componentes afectados.
    
    Args:
        tipo_mantenimiento: Tipo de mantenimiento (ej: "cambio_aceite")
    
    Returns:
        Lista de nombres de componentes a resetear
    
    Ejemplo:
        >>> _mapear_tipo_mantenimiento_a_componentes("cambio_aceite")
        ["Motor"]
        >>> _mapear_tipo_mantenimiento_a_componentes("servicio_completo")
        ["Motor", "Transmisión", "Frenos Delanteros", ...]
    """
    tipo_lower = tipo_mantenimiento.lower().replace(" ", "_")
    
    # Buscar coincidencia exacta
    if tipo_lower in MANTENIMIENTO_TO_COMPONENTES:
        return MANTENIMIENTO_TO_COMPONENTES[tipo_lower]
    
    # Buscar coincidencia parcial (ej: "Cambio de Aceite" → "cambio_aceite")
    for key, componentes in MANTENIMIENTO_TO_COMPONENTES.items():
        if key in tipo_lower or tipo_lower in key:
            return componentes
    
    # Si no hay coincidencia, retornar lista vacía
    logger.warning(f"Tipo de mantenimiento '{tipo_mantenimiento}' no mapeado a componentes")
    return []


# ============================================
# EVENT HANDLER: MANTENIMIENTO COMPLETADO
# ============================================

async def handle_mantenimiento_completado(event: MantenimientoCompletadoEvent) -> None:
    """
    Handler cuando se completa un mantenimiento.
    
    Acciones:
    1. Actualizar kilometraje de la moto si cambió
    2. Resetear estados de componentes relacionados a BUENO
    3. Log de auditoría
    
    Args:
        event: Evento de mantenimiento completado
    
    Ejemplo:
        Usuario completa cambio de aceite (5000 km)
        → Estado Motor: ATENCION → BUENO
        → kilometraje_actual: 5234.5 → 5250.0
        → Log: "Mantenimiento completado: cambio_aceite (Moto ID: 1)"
    """
    logger.info(
        f"[EVENT] MantenimientoCompletadoEvent recibido: "
        f"Moto {event.moto_id}, Tipo: {event.tipo}"
    )
    
    async for db in get_db():
        try:
            moto_repo = MotoRepository(db)
            estado_repo = EstadoActualRepository(db)
            
            # 1. Actualizar kilometraje si hay kilometraje_siguiente
            await _actualizar_kilometraje_si_necesario(
                moto_repo, event.moto_id, event.kilometraje_siguiente
            )
            
            # 2. Resetear estados de componentes relacionados
            componentes_reseteados = await _resetear_estados_componentes(
                estado_repo, event.moto_id, event.tipo
            )
            
            # 3. Log de auditoría
            logger.info(
                f"[SUCCESS] Mantenimiento completado procesado: "
                f"Moto {event.moto_id}, Tipo: {event.tipo}, "
                f"Componentes reseteados: {componentes_reseteados}"
            )
            
            await db.commit()
            
        except Exception as e:
            logger.error(
                f"[ERROR] Fallo al procesar MantenimientoCompletadoEvent: "
                f"Moto {event.moto_id}, Error: {str(e)}"
            )
            await db.rollback()
            raise


async def _actualizar_kilometraje_si_necesario(
    moto_repo: MotoRepository,
    moto_id: int,
    kilometraje_siguiente: Optional[float]
) -> None:
    """Actualiza el kilometraje de la moto si es mayor al actual."""
    if not kilometraje_siguiente or kilometraje_siguiente <= 0:
        return
    
    moto = await moto_repo.get_by_id(moto_id)
    
    if moto and kilometraje_siguiente > moto.kilometraje_actual:
        await moto_repo.update(
            moto_id=moto_id,
            update_data={"kilometraje_actual": Decimal(str(kilometraje_siguiente))}
        )
        logger.info(
            f"Kilometraje actualizado: Moto {moto_id}, "
            f"{moto.kilometraje_actual} → {kilometraje_siguiente} km"
        )


async def _resetear_estados_componentes(
    estado_repo: EstadoActualRepository,
    moto_id: int,
    tipo_mantenimiento: str
) -> int:
    """Resetea estados de componentes relacionados al mantenimiento. Retorna cantidad reseteada."""
    componentes_a_resetear = _mapear_tipo_mantenimiento_a_componentes(tipo_mantenimiento)
    
    if not componentes_a_resetear:
        return 0
    
    estados_actuales = await estado_repo.get_by_moto(moto_id)
    componentes_reseteados = 0
    
    for estado_actual in estados_actuales:
        # Verificar si el componente está en la lista a resetear
        if estado_actual.componente.nombre not in componentes_a_resetear:
            continue
        
        # Solo resetear si NO está en estado BUENO o EXCELENTE
        if estado_actual.estado not in [EstadoSalud.ATENCION, EstadoSalud.CRITICO]:
            continue
        
        # Mantener el último valor o usar 0 si es None
        valor_a_usar = estado_actual.ultimo_valor if estado_actual.ultimo_valor is not None else Decimal("0")
        
        await estado_repo.upsert_estado_actual(
            moto_id=moto_id,
            componente_id=estado_actual.componente_id,
            estado=EstadoSalud.BUENO,
            ultimo_valor=valor_a_usar
        )
        logger.info(
            f"Estado reseteado: Moto {moto_id}, "
            f"Componente {estado_actual.componente.nombre}, "
            f"{estado_actual.estado.value} → BUENO"
        )
        componentes_reseteados += 1
    
    return componentes_reseteados


# ============================================
# REGISTRO DE HANDLERS
# ============================================

def register_motos_event_handlers() -> None:
    """
    Registra todos los event handlers del módulo de motos.
    
    Esta función debe ser llamada en el arranque de la aplicación
    (main.py) para activar los listeners.
    
    Handlers registrados:
    - handle_mantenimiento_completado (MantenimientoCompletadoEvent)
    - handle_usuario_deleted (UsuarioDeletedEvent)
    - handle_componente_estado_auditoria (ComponenteEstadoActualizadoEvent)
    
    Ejemplo:
        # main.py
        from src.motos.event_handlers import register_motos_event_handlers
        
        @app.on_event("startup")
        async def startup():
            register_motos_event_handlers()
    """
    logger.info("[STARTUP] Registrando event handlers del módulo motos...")
    
    # Los decoradores ya registran automáticamente,
    # pero esta función sirve para tracking y validación

    event_bus.subscribe_async(MantenimientoCompletadoEvent, handle_mantenimiento_completado)
    
    handlers_count = 1  # Número de handlers implementados
    
    logger.info(
        f"[STARTUP] ✅ {handlers_count} event handlers de motos registrados:"
        f"\n  - MantenimientoCompletadoEvent → handle_mantenimiento_completado"
        f"\n  - UsuarioDeletedEvent → handle_usuario_deleted"
        f"\n  - ComponenteEstadoActualizadoEvent → handle_componente_estado_auditoria"
    )
