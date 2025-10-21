"""
Casos de uso del módulo chatbot.
"""
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.services import ChatbotService
from src.chatbot.repositories import ConversacionRepository, MensajeRepository
from src.chatbot.models import Conversacion, Mensaje
from src.chatbot import events, validators
from src.chatbot.schemas import ConversacionFilterParams
from src.shared.event_bus import event_bus
from src.shared.base_models import PaginationParams


class CreateConversacionUseCase:
    """Caso de uso para crear una nueva conversación."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        usuario_id: int,
        titulo: str,
        nivel_acceso: str,
        moto_id: Optional[int] = None
    ) -> Conversacion:
        """
        Crea una nueva conversación.
        
        Args:
            usuario_id: ID del usuario
            titulo: Título de la conversación
            nivel_acceso: "freemium" o "premium"
            moto_id: ID de la moto (opcional)
            
        Returns:
            Conversación creada
        """
        # Validar nivel de acceso
        if not validators.validate_nivel_acceso(nivel_acceso):
            raise ValueError(f"Nivel de acceso inválido: {nivel_acceso}")
        
        # Crear conversación
        conversacion = await self.service.create_conversacion(
            usuario_id=usuario_id,
            titulo=titulo,
            nivel_acceso=nivel_acceso,
            moto_id=moto_id
        )
        
        # Emitir evento
        await event_bus.publish(events.ConversacionIniciadaEvent(
            conversation_id=conversacion.conversation_id,
            usuario_id=usuario_id,
            nivel_acceso=nivel_acceso
        ))
        
        return conversacion


class SendMessageUseCase:
    """Caso de uso para enviar un mensaje al chatbot."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        usuario_id: int,
        message: str,
        conversation_id: Optional[str] = None,
        nivel_acceso: str = "freemium",
        moto_id: Optional[int] = None,
        tipo_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Conversacion, Mensaje]:
        """
        Envía un mensaje al chatbot y obtiene respuesta.
        
        Args:
            usuario_id: ID del usuario
            message: Mensaje del usuario
            conversation_id: ID de conversación existente (opcional)
            nivel_acceso: "freemium" o "premium"
            moto_id: ID de la moto (opcional)
            tipo_prompt: Tipo de prompt (diagnostic/maintenance/explanation)
            context: Contexto adicional (sensores, fallas, etc.)
            
        Returns:
            Tuple con (respuesta, conversacion, mensaje_asistente)
        """
        # Validar mensaje
        if not validators.validate_message_length(message):
            raise ValueError("Mensaje demasiado largo (máximo 2000 caracteres)")
        
        # Emitir evento de mensaje enviado
        await event_bus.publish(events.MensajeEnviadoEvent(
            conversation_id=conversation_id or "nuevo",
            usuario_id=usuario_id,
            contenido=message
        ))
        
        try:
            # Procesar mensaje
            response, conversacion, mensaje_asistente = await self.service.process_message(
                usuario_id=usuario_id,
                message=message,
                conversation_id=conversation_id,
                nivel_acceso=nivel_acceso,
                moto_id=moto_id,
                tipo_prompt=tipo_prompt,
                context=context
            )
            
            # Emitir evento de respuesta generada
            await event_bus.publish(events.RespuestaGeneradaEvent(
                conversation_id=conversacion.conversation_id,
                mensaje_id=mensaje_asistente.id,
                tokens=mensaje_asistente.tokens_usados or 0,
                tiempo_ms=mensaje_asistente.tiempo_respuesta_ms or 0,
                modelo=mensaje_asistente.modelo_usado or "unknown"
            ))
            
            return response, conversacion, mensaje_asistente
            
        except ValueError as e:
            # Límite alcanzado
            await event_bus.publish(events.LimiteAlcanzadoEvent(
                usuario_id=usuario_id,
                tipo_limite="mensajes_diarios",
                nivel_acceso=nivel_acceso
            ))
            raise
        except Exception as e:
            # Error general
            await event_bus.publish(events.ErrorChatbotEvent(
                conversation_id=conversation_id or "nuevo",
                usuario_id=usuario_id,
                error_type=type(e).__name__,
                error_message=str(e)
            ))
            raise


class SendMessageStreamUseCase:
    """Caso de uso para enviar mensaje con streaming."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        usuario_id: int,
        message: str,
        conversation_id: Optional[str] = None,
        nivel_acceso: str = "freemium",
        moto_id: Optional[int] = None,
        tipo_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Envía mensaje y hace streaming de la respuesta.
        
        Yields:
            Chunks de texto de la respuesta
        """
        # Validar mensaje
        if not validators.validate_message_length(message):
            raise ValueError("Mensaje demasiado largo")
        
        # Emitir evento
        await event_bus.publish(events.MensajeEnviadoEvent(
            conversation_id=conversation_id or "nuevo",
            usuario_id=usuario_id,
            contenido=message
        ))
        
        try:
            async for chunk in self.service.process_message_stream(
                usuario_id=usuario_id,
                message=message,
                conversation_id=conversation_id,
                nivel_acceso=nivel_acceso,
                moto_id=moto_id,
                tipo_prompt=tipo_prompt,
                context=context
            ):
                yield chunk
                
        except ValueError:
            # Límite alcanzado
            await event_bus.publish(events.LimiteAlcanzadoEvent(
                usuario_id=usuario_id,
                tipo_limite="mensajes_diarios",
                nivel_acceso=nivel_acceso
            ))
            raise
        except Exception as e:
            await event_bus.publish(events.ErrorChatbotEvent(
                conversation_id=conversation_id or "nuevo",
                usuario_id=usuario_id,
                error_type=type(e).__name__,
                error_message=str(e)
            ))
            raise


class GetConversacionUseCase:
    """Caso de uso para obtener una conversación con mensajes."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)

    async def execute(
        self,
        conversation_id: str,
        usuario_id: int,
        limit: int = 50
    ) -> tuple[Conversacion, List[Mensaje]]:
        """
        Obtiene una conversación con sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
            limit: Límite de mensajes
            
        Returns:
            Tuple con (conversacion, mensajes)
        """
        # Obtener conversación
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        if not conversacion:
            raise ValueError(f"Conversación {conversation_id} no encontrada")
        
        # Verificar que pertenece al usuario
        if conversacion.usuario_id != usuario_id:
            raise ValueError("No tienes acceso a esta conversación")
        
        # Obtener mensajes
        mensajes = await self.mensaje_repo.get_by_conversacion(
            conversacion.id,
            limit=limit
        )
        
        return conversacion, mensajes


class ListConversacionesByUsuarioUseCase:
    """Caso de uso para listar conversaciones de un usuario."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)

    async def execute(
        self,
        filters: ConversacionFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Conversacion], int]:
        """
        Lista las conversaciones de un usuario con paginación.
        
        Args:
            filters: Filtros a aplicar
            pagination: Parámetros de paginación
            
        Returns:
            Tuple con (conversaciones, total)
        """
        if filters.solo_activas:
            conversaciones = await self.conversacion_repo.get_activas(
                filters.usuario_id,  # type: ignore
                skip=pagination.offset,
                limit=pagination.limit
            )
        else:
            conversaciones = await self.conversacion_repo.get_by_usuario(
                filters.usuario_id,  # type: ignore
                skip=pagination.offset,
                limit=pagination.limit
            )
        
        total = await self.conversacion_repo.count_by_usuario(
            filters.usuario_id,  # type: ignore
            solo_activas=filters.solo_activas or False
        )
        
        return conversaciones, total


class AddFeedbackUseCase:
    """Caso de uso para agregar feedback a un mensaje."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        mensaje_id: int,
        usuario_id: int,
        util: bool,
        feedback: Optional[str] = None
    ) -> Mensaje:
        """
        Agrega feedback a un mensaje del asistente.
        
        Args:
            mensaje_id: ID del mensaje
            usuario_id: ID del usuario (para verificar acceso)
            util: Si la respuesta fue útil
            feedback: Comentario adicional
            
        Returns:
            Mensaje actualizado
        """
        # Obtener mensaje
        mensaje = await self.mensaje_repo.get_by_id(mensaje_id)
        if not mensaje:
            raise ValueError(f"Mensaje {mensaje_id} no encontrado")
        
        # Verificar que sea del asistente
        if mensaje.role != "assistant":
            raise ValueError("Solo se puede dar feedback a mensajes del asistente")
        
        # Verificar acceso a la conversación
        conversacion = await self.conversacion_repo.get_by_id(mensaje.conversacion_id)
        if not conversacion or conversacion.usuario_id != usuario_id:
            raise ValueError("No tienes acceso a esta conversación")
        
        # Agregar feedback
        mensaje_actualizado = await self.service.add_feedback(
            mensaje_id=mensaje_id,
            util=util,
            feedback=feedback
        )
        
        # Emitir evento
        await event_bus.publish(events.FeedbackRecibidoEvent(
            mensaje_id=mensaje_id,
            util=util,
            feedback=feedback or ""
        ))
        
        return mensaje_actualizado


class ClearHistoryUseCase:
    """Caso de uso para limpiar el historial de una conversación."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(self, conversacion_id: int, usuario_id: int) -> None:
        """
        Limpia el historial de mensajes de una conversación.
        
        Args:
            conversacion_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
        """
        await self.service.clear_conversacion_history(conversacion_id, usuario_id)


class DeleteConversacionUseCase:
    """Caso de uso para eliminar una conversación."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)

    async def execute(self, conversation_id: str, usuario_id: int) -> None:
        """
        Elimina una conversación y sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
        """
        # Obtener conversación
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        if not conversacion:
            raise ValueError(f"Conversación {conversation_id} no encontrada")
        
        # Verificar acceso
        if not validators.can_delete_conversation(usuario_id, conversacion.usuario_id):
            raise ValueError("No tienes permiso para eliminar esta conversación")
        
        # Eliminar
        await self.conversacion_repo.delete(conversacion.id)
        
        # Emitir evento
        await event_bus.publish(events.ConversacionFinalizadaEvent(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            total_mensajes=conversacion.total_mensajes or 0
        ))


class GetStatsUseCase:
    """Caso de uso para obtener estadísticas del chatbot."""

    def __init__(self, session: AsyncSession):
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas del chatbot.
        
        Args:
            usuario_id: ID del usuario (None para stats globales, solo admin)
            
        Returns:
            Diccionario con estadísticas
        """
        return await self.service.get_conversacion_stats(usuario_id)
