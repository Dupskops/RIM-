"""
Casos de uso del módulo chatbot.

Alineado con MVP v2.3 - Sistema de límites Freemium.
Incluye integración con tabla uso_caracteristicas para control de límites.
"""
from typing import Optional, List, Dict, Any, AsyncGenerator, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatbot.services import ChatbotService
from src.chatbot.repositories import ConversacionRepository, MensajeRepository
from src.chatbot.models import Conversacion, Mensaje, TipoPrompt
from src.chatbot import events
from src.chatbot.schemas import ConversacionFilterParams
from src.shared.event_bus import event_bus
from src.shared.base_models import PaginationParams
from src.chatbot import validators


class CheckChatbotLimitUseCase:
    """
    Caso de uso para verificar límites de conversaciones del chatbot.
    
    Free: 5 conversaciones/mes
    Pro: Ilimitadas
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, usuario_id: int) -> Dict[str, Any]:
        """
        Verifica el límite de conversaciones para el usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Dict con información del límite:
            {
                "puede_crear": bool,
                "usos_realizados": int,
                "limite_mensual": int,
                "usos_restantes": int,
                "es_pro": bool,
                "periodo_mes": date
            }
        """
        # Obtener información del plan del usuario
        query = """
            SELECT 
                p.nombre_plan,
                c.limite_free,
                c.limite_pro
            FROM usuarios u
            JOIN suscripciones s ON s.usuario_id = u.id AND s.estado_suscripcion = 'activa'
            JOIN planes p ON p.id = s.plan_id
            CROSS JOIN caracteristicas c
            WHERE u.id = :usuario_id 
            AND c.clave_funcion = 'CHATBOT'
            AND u.deleted_at IS NULL
        """
        
        result = await self.session.execute(
            query,
            {"usuario_id": usuario_id}
        )
        row = result.fetchone()
        
        if not row:
            raise ValueError(f"Usuario {usuario_id} no encontrado o sin plan activo")
        
        nombre_plan, limite_free, _ = row
        es_pro = nombre_plan == 'pro'
        
        # Si es Pro, no hay límites
        if es_pro:
            return {
                "puede_crear": True,
                "usos_realizados": 0,
                "limite_mensual": None,  # Ilimitado
                "usos_restantes": None,  # Ilimitado
                "es_pro": True,
                "periodo_mes": date.today().replace(day=1)
            }
        
        # Para usuarios Free, verificar uso actual
        periodo_actual = date.today().replace(day=1)
        
        query_uso = """
            SELECT 
                COALESCE(uc.usos_realizados, 0) as usos,
                :limite_free as limite
            FROM usuarios u
            LEFT JOIN uso_caracteristicas uc ON 
                uc.usuario_id = u.id 
                AND uc.periodo_mes = :periodo_mes
                AND uc.caracteristica_id = (
                    SELECT id FROM caracteristicas WHERE clave_funcion = 'CHATBOT'
                )
                AND uc.deleted_at IS NULL
            WHERE u.id = :usuario_id
        """
        
        result_uso = await self.session.execute(
            query_uso,
            {
                "usuario_id": usuario_id,
                "periodo_mes": periodo_actual,
                "limite_free": limite_free
            }
        )
        row_uso = result_uso.fetchone()
        
        if not row_uso:
            usos_realizados = 0
            limite = limite_free
        else:
            usos_realizados, limite = row_uso
        
        usos_restantes = limite - usos_realizados
        puede_crear = usos_restantes > 0
        
        return {
            "puede_crear": puede_crear,
            "usos_realizados": usos_realizados,
            "limite_mensual": limite,
            "usos_restantes": usos_restantes,
            "es_pro": False,
            "periodo_mes": periodo_actual
        }


class RegisterChatbotUsageUseCase:
    """
    Caso de uso para registrar el uso de una conversación del chatbot.
    
    Incrementa el contador en uso_caracteristicas.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, usuario_id: int) -> None:
        """
        Registra el uso de una conversación del chatbot.
        
        Args:
            usuario_id: ID del usuario
        """
        # Llamar a la función PostgreSQL para registrar uso
        query = """
            SELECT registrar_uso_caracteristica(
                :usuario_id,
                'CHATBOT'
            )
        """
        
        await self.session.execute(
            query,
            {"usuario_id": usuario_id}
        )
        await self.session.commit()


class CreateConversacionUseCase:
    """Caso de uso para crear una nueva conversación."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)
        self.check_limit_uc = CheckChatbotLimitUseCase(session)
        self.register_usage_uc = RegisterChatbotUsageUseCase(session)

    async def execute(
        self,
        usuario_id: int,
        moto_id: int,
        titulo: Optional[str] = None
    ) -> Conversacion:
        """
        Crea una nueva conversación verificando límites Freemium.
        
        Args:
            usuario_id: ID del usuario
            moto_id: ID de la moto
            titulo: Título opcional
            
        Returns:
            Conversación creada
            
        Raises:
            ValueError: Si se alcanzó el límite mensual
        """
        # 1. Verificar límites
        limite_info = await self.check_limit_uc.execute(usuario_id)
        
        if not limite_info["puede_crear"]:
            raise ValueError(
                f"Límite de conversaciones alcanzado: "
                f"{limite_info['usos_realizados']}/{limite_info['limite_mensual']} usado este mes. "
                f"Actualiza a Plan Pro para conversaciones ilimitadas."
            )
        
        # 2. Crear conversación
        conversacion = await self.service.create_conversacion(
            usuario_id=usuario_id,
            moto_id=moto_id,
            titulo=titulo
        )
        
        # 3. Registrar uso (solo para usuarios Free)
        if not limite_info["es_pro"]:
            await self.register_usage_uc.execute(usuario_id)
        
        # 4. Emitir evento
        await event_bus.publish(events.ConversacionIniciadaEvent(
            conversation_id=conversacion.conversation_id,
            usuario_id=usuario_id,
            moto_id=moto_id
        ))
        
        return conversacion


class SendMessageUseCase:
    """Caso de uso para enviar un mensaje al chatbot."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        usuario_id: int,
        message: str,
        moto_id: int,
        conversation_id: Optional[str] = None,
        tipo_prompt: Optional[TipoPrompt] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Conversacion, Mensaje, Mensaje]:
        """
        Envía un mensaje al chatbot y obtiene respuesta.
        
        Args:
            usuario_id: ID del usuario
            moto_id: ID de la moto
            message: Mensaje del usuario
            conversation_id: ID de conversación existente (opcional)
            tipo_prompt: Tipo de prompt (se detecta automáticamente si no se provee)
            context: Contexto adicional (sensores, fallas, etc.)
            
        Returns:
            Tuple con (respuesta, conversacion, mensaje_usuario, mensaje_asistente)
        """
        import time
        import logging
        logger = logging.getLogger(__name__)
        start_time = time.time()
        logger.info(f"[DEBUG] SendMessageUseCase.execute iniciado. Usuario: {usuario_id}")

        # Validar mensaje usando validators
        if not validators.validate_message_length(message):
            raise ValueError("El mensaje debe tener entre 1 y 2000 caracteres")
        
        # Validar contexto si se proporciona
        if context and not validators.validate_context_data(context):
            raise ValueError("El contexto proporcionado es inválido o excede el tamaño máximo")
        
        # Emitir evento de mensaje enviado
        await event_bus.publish(events.MensajeEnviadoEvent(
            conversation_id=conversation_id or "nuevo",
            usuario_id=usuario_id,
            contenido=message
        ))
        
        try:
            # Obtener o crear conversación
            # Nota: El título definitivo se genera automáticamente en process_message
            # con contexto completo (mensaje usuario + respuesta asistente)
            conversacion = await self.service.get_or_create_conversacion(
                usuario_id=usuario_id,
                moto_id=moto_id,
                conversation_id=conversation_id,
                titulo=None  # Se genera automáticamente después del primer intercambio
            )
            
            # Procesar mensaje
            response, mensaje_usuario, mensaje_asistente = await self.service.process_message(
                conversacion=conversacion,
                message=message,
                context=context,
                tipo_prompt_override=tipo_prompt
            )
            
            # Emitir evento de respuesta generada
            await event_bus.publish(events.RespuestaGeneradaEvent(
                conversation_id=conversacion.conversation_id,
                mensaje_id=mensaje_asistente.id,
                tipo_prompt=mensaje_asistente.tipo_prompt.value if mensaje_asistente.tipo_prompt else "general"
            ))
            
            return response, conversacion, mensaje_usuario, mensaje_asistente
            
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
    """Caso de uso para enviar mensaje con streaming de respuesta."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        usuario_id: int,
        message: str,
        moto_id: int,
        conversation_id: Optional[str] = None,
        tipo_prompt: Optional[TipoPrompt] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Envía mensaje y hace streaming de la respuesta.
        
        Args:
            usuario_id: ID del usuario
            moto_id: ID de la moto
            message: Mensaje del usuario
            conversation_id: ID de conversación existente (opcional)
            tipo_prompt: Tipo de prompt
            context: Contexto adicional
            
        Yields:
            Chunks de texto de la respuesta
        """
        # Validar mensaje usando validators
        if not validators.validate_message_length(message):
            raise ValueError("El mensaje debe tener entre 1 y 2000 caracteres")
        
        # Validar contexto si se proporciona
        if context and not validators.validate_context_data(context):
            raise ValueError("El contexto proporcionado es inválido o excede el tamaño máximo")
        
        # Emitir evento
        await event_bus.publish(events.MensajeEnviadoEvent(
            conversation_id=conversation_id or "nuevo",
            usuario_id=usuario_id,
            contenido=message
        ))
        
        try:
            # Obtener o crear conversación
            # Nota: El título definitivo se genera automáticamente en process_message_stream
            # con contexto completo (mensaje usuario + respuesta asistente)
            conversacion = await self.service.get_or_create_conversacion(
                usuario_id=usuario_id,
                moto_id=moto_id,
                conversation_id=conversation_id,
                titulo=None  # Se genera automáticamente después del primer intercambio
            )
            
            # Stream de respuesta
            async for chunk in self.service.process_message_stream(
                conversacion=conversacion,
                message=message,
                context=context,
                tipo_prompt_override=tipo_prompt
            ):
                yield chunk
                
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
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        conversation_id: str,
        usuario_id: int,
        limit: int = 50
    ) -> Tuple[Conversacion, List[Mensaje]]:
        """
        Obtiene una conversación con sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
            limit: Límite de mensajes
            
        Returns:
            Tuple con (conversacion, mensajes)
        """
        return await self.service.get_conversacion_with_messages(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            limit=limit
        )


class ListConversacionesByUsuarioUseCase:
    """Caso de uso para listar conversaciones de un usuario."""

    def __init__(self, session: AsyncSession):
        self.session = session
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
        if not filters.usuario_id:
            raise ValueError("usuario_id es requerido")
        
        if filters.solo_activas:
            conversaciones = await self.conversacion_repo.get_activas(
                filters.usuario_id,
                skip=pagination.offset,
                limit=pagination.limit
            )
        else:
            conversaciones = await self.conversacion_repo.get_by_usuario(
                filters.usuario_id,
                skip=pagination.offset,
                limit=pagination.limit
            )
        
        total = await self.conversacion_repo.count_by_usuario(
            filters.usuario_id,
            solo_activas=filters.solo_activas or False
        )
        
        return conversaciones, total


class ArchivarConversacionUseCase:
    """Caso de uso para archivar una conversación."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        conversation_id: str,
        usuario_id: int
    ) -> Conversacion:
        """
        Archiva una conversación (la marca como inactiva).
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
            
        Returns:
            Conversación archivada
        """
        conversacion = await self.service.archivar_conversacion(
            conversation_id=conversation_id,
            usuario_id=usuario_id
        )
        
        # Emitir evento
        await event_bus.publish(events.ConversacionFinalizadaEvent(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            total_mensajes=conversacion.total_mensajes
        ))
        
        return conversacion


class DeleteConversacionUseCase:
    """Caso de uso para eliminar una conversación."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(
        self,
        conversation_id: str,
        usuario_id: int
    ) -> None:
        """
        Elimina una conversación y sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para verificar acceso)
        """
        # Obtener conversación antes de eliminar (para evento)
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        
        if not conversacion:
            raise ValueError(f"Conversación {conversation_id} no encontrada")
        
        total_mensajes = conversacion.total_mensajes
        
        # Eliminar
        await self.service.delete_conversacion(
            conversation_id=conversation_id,
            usuario_id=usuario_id
        )
        
        # Emitir evento
        await event_bus.publish(events.ConversacionFinalizadaEvent(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            total_mensajes=total_mensajes
        ))


class GetStatsUseCase:
    """Caso de uso para obtener estadísticas del chatbot."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversacion_repo = ConversacionRepository(session)
        self.mensaje_repo = MensajeRepository(session)
        self.service = ChatbotService(self.conversacion_repo, self.mensaje_repo)

    async def execute(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas del chatbot del usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        return await self.service.get_conversacion_stats(usuario_id)
