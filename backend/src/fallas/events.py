"""
Eventos de dominio para el módulo de fallas (MVP v2.3).

Los eventos se emiten cuando ocurren acciones importantes en el ciclo de vida de una falla.
Estos eventos pueden ser consumidos por:
- Sistema de notificaciones (enviar alertas al usuario)
- Webhooks
- Análisis ML (patrones de fallas)
- Auditoría
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class FallaDetectadaEvent:
    """
    Evento emitido cuando se detecta/crea una nueva falla.
    
    Usado para:
    - Enviar notificación al usuario
    - Actualizar dashboard en tiempo real (WebSocket)
    - Registrar en sistema de auditoría
    - Trigger análisis ML si es usuario Pro
    """
    falla_id: int
    moto_id: int
    componente_id: int
    tipo: str
    severidad: str  # "baja", "media", "alta", "critica"
    puede_conducir: bool
    requiere_atencion_inmediata: bool
    usuario_id: int  # 0 si es detección automática
    origen: str  # "sensor", "ml", "manual"
    timestamp: Optional[datetime]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    async def emit(self):
        """
        Emite el evento al sistema de eventos.
        
        TODO: Implementar integración con:
        - Redis Pub/Sub
        - Sistema de notificaciones
        - WebSocket broadcast
        """
        # Por ahora solo logging
        print(f"[EVENT] FallaDetectada: falla_id={self.falla_id}, tipo={self.tipo}, severidad={self.severidad}")
        
        # Aquí iría la lógica real:
        # await event_bus.publish("falla.detectada", self)
        # await notificaciones_service.crear_notificacion(self)
        # await websocket_manager.broadcast(f"moto:{self.moto_id}", self)


@dataclass
class FallaActualizadaEvent:
    """
    Evento emitido cuando se actualiza una falla (cambio de estado, severidad, etc.).
    
    Usado para:
    - Notificar cambios al usuario
    - Actualizar dashboard
    - Registro de auditoría
    """
    falla_id: int
    moto_id: int
    tipo: str
    estado_anterior: str
    estado_nuevo: str
    usuario_id: int
    timestamp: Optional[datetime]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    async def emit(self):
        """Emite el evento de actualización."""
        print(f"[EVENT] FallaActualizada: falla_id={self.falla_id}, {self.estado_anterior} -> {self.estado_nuevo}")
        
        # Aquí iría la lógica real:
        # await event_bus.publish("falla.actualizada", self)
        # if self.estado_nuevo == "en_reparacion":
        #     await notificaciones_service.notificar_inicio_reparacion(self)


@dataclass
class FallaResueltaEvent:
    """
    Evento emitido cuando se resuelve una falla (estado -> RESUELTA).
    
    Usado para:
    - Notificar resolución al usuario
    - Actualizar métricas y estadísticas
    - Cerrar tickets relacionados
    - Actualizar estado del componente a BUENO
    """
    falla_id: int
    moto_id: int
    tipo: str
    solucion_aplicada: str  # Vacío en v2.3 (se maneja en mantenimientos)
    costo_real: float  # 0.0 en v2.3 (se maneja en mantenimientos)
    dias_resolucion: int
    usuario_id: int
    timestamp: Optional[datetime]
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    async def emit(self):
        """Emite el evento de resolución."""
        print(f"[EVENT] FallaResuelta: falla_id={self.falla_id}, dias={self.dias_resolucion}")
        
        # Aquí iría la lógica real:
        # await event_bus.publish("falla.resuelta", self)
        # await notificaciones_service.notificar_falla_resuelta(self)
        # await componentes_service.actualizar_estado_componente(self.componente_id, "BUENO")
        # await metrics_service.registrar_tiempo_resolucion(self.dias_resolucion)


# Eventos futuros (v2.4+):
# - FallaPredictedByMLEvent: cuando ML predice una falla potencial
# - FallaEscaladaEvent: cuando una falla baja se vuelve crítica
# - FallaIgnoradaEvent: cuando se marca una falla como falso positivo
