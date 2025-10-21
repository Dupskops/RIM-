"""
Servicios de lógica de negocio para el chatbot.
"""
import uuid
import time
from typing import Optional, AsyncGenerator, Dict, Any
from datetime import datetime

from src.chatbot.repositories import ConversacionRepository, MensajeRepository
from src.chatbot.models import Conversacion, Mensaje
from src.chatbot import validators
from src.chatbot.prompts.diagnostic_prompt import (
    DIAGNOSTIC_SYSTEM_PROMPT,
    build_diagnostic_prompt,
    build_quick_diagnostic_prompt
)
from src.chatbot.prompts.maintenance_prompt import (
    MAINTENANCE_SYSTEM_PROMPT,
    build_maintenance_recommendation_prompt
)
from src.chatbot.prompts.explanation_prompt import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt
)
from src.integraciones.llm_provider import get_llm_provider


class ChatbotService:
    """Servicio principal para el chatbot."""

    def __init__(self, conversacion_repo: ConversacionRepository, mensaje_repo: MensajeRepository):
        self.conversacion_repo = conversacion_repo
        self.mensaje_repo = mensaje_repo
        self.llm_provider = get_llm_provider()

    async def create_conversacion(
        self,
        usuario_id: int,
        titulo: str,
        nivel_acceso: str,
        moto_id: Optional[int] = None
    ) -> Conversacion:
        """Crea una nueva conversación."""
        conversation_id = f"conv_{uuid.uuid4().hex[:16]}"
        
        conversacion = Conversacion(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            moto_id=moto_id,
            titulo=titulo,
            nivel_acceso=nivel_acceso,
            activa=True,
            total_mensajes=0,
            ultima_actividad=datetime.utcnow()
        )
        
        return await self.conversacion_repo.create(conversacion)

    async def get_or_create_conversacion(
        self,
        usuario_id: int,
        conversation_id: Optional[str],
        nivel_acceso: str,
        moto_id: Optional[int] = None
    ) -> Conversacion:
        """Obtiene una conversación existente o crea una nueva."""
        if conversation_id:
            conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
            if conversacion and conversacion.usuario_id == usuario_id:
                return conversacion
        
        # Crear nueva conversación
        titulo = f"Conversación {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        return await self.create_conversacion(usuario_id, titulo, nivel_acceso, moto_id)

    async def process_message(
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
        Procesa un mensaje del usuario y genera respuesta.
        
        Returns:
            Tuple con (respuesta, conversacion, mensaje_asistente)
        """
        # Verificar límites
        mensajes_hoy = await self.mensaje_repo.count_by_usuario_hoy(usuario_id)
        if nivel_acceso == "freemium":
            if not validators.can_send_message_freemium(mensajes_hoy):
                raise ValueError("Límite diario de mensajes alcanzado (Freemium: 50/día)")
        else:
            if not validators.can_send_message_premium(mensajes_hoy):
                raise ValueError("Límite diario de mensajes alcanzado (Premium: 1000/día)")
        
        # Obtener o crear conversación
        conversacion = await self.get_or_create_conversacion(
            usuario_id, conversation_id, nivel_acceso, moto_id
        )
        
        # Guardar mensaje del usuario
        mensaje_usuario = Mensaje(
            conversacion_id=conversacion.id,
            role="user",
            contenido=message
        )
        await self.mensaje_repo.create(mensaje_usuario)
        
        # Detectar tipo de prompt si no se especifica
        if not tipo_prompt:
            tipo_prompt = validators.detect_prompt_type(message)
        
        # Construir contexto y prompt
        system_prompt, user_prompt = await self._build_prompts(
            tipo_prompt,
            message,
            conversacion.id,
            nivel_acceso,
            context or {}
        )
        
        # Generar respuesta
        start_time = time.time()
        response = await self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=validators.get_max_tokens(nivel_acceso),
            temperature=0.7
        )
        end_time = time.time()
        
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Guardar mensaje del asistente
        mensaje_asistente = Mensaje(
            conversacion_id=conversacion.id,
            role="assistant",
            contenido=response,
            tokens_usados=len(response.split()),
            tiempo_respuesta_ms=response_time_ms,
            modelo_usado=self.llm_provider.model_name,
            tipo_prompt=tipo_prompt
        )
        await self.mensaje_repo.create(mensaje_asistente)
        
        # Actualizar conversación
        await self.conversacion_repo.actualizar_actividad(conversacion)
        
        return response, conversacion, mensaje_asistente

    async def process_message_stream(
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
        Procesa un mensaje con streaming de respuesta.
        
        Yields:
            Chunks de la respuesta del LLM
        """
        # Verificar límites
        mensajes_hoy = await self.mensaje_repo.count_by_usuario_hoy(usuario_id)
        if nivel_acceso == "freemium":
            if not validators.can_send_message_freemium(mensajes_hoy):
                raise ValueError("Límite diario de mensajes alcanzado")
        
        # Obtener o crear conversación
        conversacion = await self.get_or_create_conversacion(
            usuario_id, conversation_id, nivel_acceso, moto_id
        )
        
        # Guardar mensaje del usuario
        mensaje_usuario = Mensaje(
            conversacion_id=conversacion.id,
            role="user",
            contenido=message
        )
        await self.mensaje_repo.create(mensaje_usuario)
        
        # Detectar tipo de prompt
        if not tipo_prompt:
            tipo_prompt = validators.detect_prompt_type(message)
        
        # Construir prompts
        system_prompt, user_prompt = await self._build_prompts(
            tipo_prompt,
            message,
            conversacion.id,
            nivel_acceso,
            context or {}
        )
        
        # Stream de respuesta
        response_chunks = []
        start_time = time.time()
        
        async for chunk in self.llm_provider.generate_stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=validators.get_max_tokens(nivel_acceso),
            temperature=0.7
        ):
            response_chunks.append(chunk)
            yield chunk
        
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Guardar respuesta completa
        full_response = "".join(response_chunks)
        mensaje_asistente = Mensaje(
            conversacion_id=conversacion.id,
            role="assistant",
            contenido=full_response,
            tokens_usados=len(full_response.split()),
            tiempo_respuesta_ms=response_time_ms,
            modelo_usado=self.llm_provider.model_name,
            tipo_prompt=tipo_prompt
        )
        await self.mensaje_repo.create(mensaje_asistente)
        
        # Actualizar conversación
        await self.conversacion_repo.actualizar_actividad(conversacion)

    async def _build_prompts(
        self,
        tipo_prompt: str,
        message: str,
        conversacion_id: int,
        nivel_acceso: str,
        context: Dict[str, Any]
    ) -> tuple[str, str]:
        """Construye los prompts del sistema y usuario."""
        # Obtener historial de contexto
        max_context = validators.get_max_context_messages(nivel_acceso)
        mensajes_previos = await self.mensaje_repo.get_ultimos_mensajes(
            conversacion_id,
            limit=max_context
        )
        
        # Construir contexto de conversación
        conversation_context = "\n".join([
            f"{m.role.upper()}: {m.contenido}"
            for m in mensajes_previos
        ])
        
        # Seleccionar system prompt según tipo
        if tipo_prompt == "diagnostic":
            system_prompt = DIAGNOSTIC_SYSTEM_PROMPT
            if context and "datos_sensores" in context:
                user_prompt = build_diagnostic_prompt(
                    sintomas=message,
                    datos_sensores=context.get("datos_sensores", {}),
                    fallas_recientes=context.get("fallas_recientes", []),
                    kilometraje=context.get("kilometraje", 0),
                    modelo_moto=context.get("modelo_moto", "Desconocido")
                )
            else:
                user_prompt = build_quick_diagnostic_prompt(message)
        
        elif tipo_prompt == "maintenance":
            system_prompt = MAINTENANCE_SYSTEM_PROMPT
            if context and "mantenimientos_vencidos" in context:
                user_prompt = build_maintenance_recommendation_prompt(
                    kilometraje_actual=context.get("kilometraje_actual", 0),
                    ultimo_mantenimiento=context.get("ultimo_mantenimiento", {}),
                    mantenimientos_vencidos=context.get("mantenimientos_vencidos", []),
                    historial_fallas=context.get("historial_fallas", []),
                    patron_uso=context.get("patron_uso", {})
                )
            else:
                user_prompt = message
        
        elif tipo_prompt == "explanation":
            system_prompt = EXPLANATION_SYSTEM_PROMPT
            user_prompt = build_explanation_prompt(
                pregunta=message,
                contexto_usuario=context
            )
        
        else:  # general
            system_prompt = """Eres un asistente experto en motocicletas del sistema RIM.
Ayudas a los usuarios con información sobre sus motocicletas, mantenimiento, problemas técnicos y mejores prácticas.
Responde de forma clara, profesional y útil."""
            user_prompt = message
        
        # Agregar contexto de conversación si existe
        if conversation_context:
            user_prompt = f"""CONTEXTO DE CONVERSACIÓN PREVIA:
{conversation_context}

MENSAJE ACTUAL:
{user_prompt}"""
        
        return system_prompt, user_prompt

    async def add_feedback(
        self,
        mensaje_id: int,
        util: bool,
        feedback: Optional[str] = None
    ) -> Mensaje:
        """Agrega feedback a un mensaje del asistente."""
        mensaje = await self.mensaje_repo.get_by_id(mensaje_id)
        if not mensaje:
            raise ValueError(f"Mensaje {mensaje_id} no encontrado")
        
        if not validators.validate_feedback(util, feedback):
            raise ValueError("Feedback inválido")
        
        mensaje.util = util
        mensaje.feedback = feedback
        
        return await self.mensaje_repo.update(mensaje)

    async def clear_conversacion_history(self, conversacion_id: int, usuario_id: int) -> None:
        """Limpia el historial de una conversación."""
        conversacion = await self.conversacion_repo.get_by_id(conversacion_id)
        if not conversacion:
            raise ValueError(f"Conversación {conversacion_id} no encontrada")
        
        if not validators.can_clear_history(usuario_id, conversacion.usuario_id):
            raise ValueError("No tienes permiso para limpiar esta conversación")
        
        await self.mensaje_repo.delete_by_conversacion(conversacion_id)
        conversacion.total_mensajes = 0
        await self.conversacion_repo.update(conversacion)

    async def get_conversacion_stats(
        self,
        usuario_id: Optional[int] = None
    ) -> dict[str, Any]:
        """Obtiene estadísticas del chatbot."""
        # Total de conversaciones
        if usuario_id:
            total_conversaciones = await self.conversacion_repo.count_by_usuario(usuario_id)
            activas = await self.conversacion_repo.count_by_usuario(usuario_id, solo_activas=True)
        else:
            # Stats globales (solo admin)
            total_conversaciones = 0  # TODO: implementar
            activas = 0
        
        # Métricas de mensajes
        tiempo_promedio = await self.mensaje_repo.get_tiempo_respuesta_promedio()
        tasa_utilidad = await self.mensaje_repo.get_tasa_utilidad()
        
        return {
            "total_conversaciones": total_conversaciones,
            "conversaciones_activas": activas,
            "tiempo_respuesta_promedio_ms": tiempo_promedio or 0,
            "tasa_utilidad": tasa_utilidad,
        }


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """Genera un título basado en el primer mensaje."""
    # Limpiar y truncar
    titulo = first_message.strip()
    if len(titulo) > max_length:
        titulo = titulo[:max_length-3] + "..."
    return titulo or "Nueva conversación"
