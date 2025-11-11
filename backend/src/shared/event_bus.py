"""
Event Bus para comunicación desacoplada entre módulos.
Implementa patrón Observer/Publisher-Subscriber.
"""
from typing import Callable, Dict, List, Type, Awaitable, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


# Type aliases para mejorar legibilidad
SyncHandler = Callable[[Any], None]
AsyncHandler = Callable[[Any], Awaitable[None]]


@dataclass
class Event:
    """Clase base para todos los eventos del sistema."""
    timestamp: datetime = field(default_factory=datetime.now)
    
    async def emit(self):
        """Publica este evento al event bus."""
        await event_bus.publish(self)


class EventBus:
    """
    Bus de eventos centralizado para comunicación entre módulos.
    
    Permite que los módulos publiquen eventos y otros módulos se suscriban
    sin conocerse directamente (desacoplamiento).
    
    Ejemplo:
        # En fallas/events.py
        @dataclass
        class FallaDetectadaEvent(Event):
            moto_id: str
            tipo_falla: str
            severidad: str
        
        # En notificaciones/service.py
        def enviar_alerta(event: FallaDetectadaEvent):
            # Enviar notificación al usuario
            pass
        
        # En main.py
        event_bus.subscribe(FallaDetectadaEvent, enviar_alerta)
        
        # En fallas/service.py
        await event_bus.publish(FallaDetectadaEvent(
            moto_id="123",
            tipo_falla="sobrecalentamiento",
            severidad="alta"
        ))
    """
    
    def __init__(self):
        self._subscribers: Dict[Type[Event], List[SyncHandler]] = {}
        self._async_subscribers: Dict[Type[Event], List[AsyncHandler]] = {}
        
    def subscribe(self, event_type: Type[Event], handler: SyncHandler) -> None:
        """
        Suscribe un handler síncrono a un tipo de evento.
        
        Args:
            event_type: Clase del evento (ej: FallaDetectadaEvent)
            handler: Función que procesa el evento
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler {handler.__name__} suscrito a {event_type.__name__}")
    
    def subscribe_async(self, event_type: Type[Event], handler: AsyncHandler) -> None:
        """
        Suscribe un handler asíncrono a un tipo de evento.
        
        Args:
            event_type: Clase del evento
            handler: Función async que procesa el evento
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(handler)
        logger.info(f"Async handler {handler.__name__} suscrito a {event_type.__name__}")
    
    def unsubscribe(self, event_type: Type[Event], handler: SyncHandler | AsyncHandler) -> None:
        """Desuscribe un handler de un evento."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)  # type: ignore
        if event_type in self._async_subscribers:
            self._async_subscribers[event_type].remove(handler)  # type: ignore
    
    async def publish(self, event: Event):
        """
        Publica un evento a todos los subscribers.
        
        Args:
            event: Instancia del evento a publicar
        """
        event_type = type(event)
        logger.info(f"Publicando evento: {event_type.__name__}")
        
        # Ejecutar handlers síncronos
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error en handler {handler.__name__} "
                        f"para evento {event_type.__name__}: {e}"
                    )
        
        # Ejecutar handlers asíncronos
        if event_type in self._async_subscribers:
            tasks: List[Awaitable[None]] = []
            for handler in self._async_subscribers[event_type]:
                tasks.append(self._execute_async_handler(handler, event))
            
            # Ejecutar en paralelo sin esperar a que terminen todos
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_async_handler(self, handler: AsyncHandler, event: Event) -> None:
        """Ejecuta un handler asíncrono con manejo de errores."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"Error en async handler {handler.__name__} "
                f"para evento {type(event).__name__}: {e}"
            )
    
    def clear(self) -> None:
        """Limpia todos los subscribers (útil para testing)."""
        self._subscribers.clear()
        self._async_subscribers.clear()
    
    def get_subscribers(self, event_type: Type[Event]) -> List[SyncHandler | AsyncHandler]:
        """Obtiene todos los handlers suscritos a un evento (útil para debugging)."""
        sync_handlers = self._subscribers.get(event_type, [])
        async_handlers = self._async_subscribers.get(event_type, [])
        return sync_handlers + async_handlers  # type: ignore


# Instancia global del event bus
event_bus = EventBus()


# ============================================
# DEPENDENCY PARA FASTAPI
# ============================================
def get_event_bus() -> EventBus:
    """
    Dependencia para inyectar el Event Bus en endpoints FastAPI.
    
    Uso:
        @router.post("/example")
        async def example(event_bus: EventBus = Depends(get_event_bus)):
            await event_bus.publish(MyEvent(...))
    """
    return event_bus