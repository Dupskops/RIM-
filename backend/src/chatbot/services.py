"""
Servicios de lógica de negocio para el chatbot.

Alineado con MVP v2.3 - Sistema de límites Freemium.
Gestiona conversaciones con límite de 5/mes para usuarios Free.
"""
import uuid
from typing import Optional, AsyncGenerator, Dict, Any, List
from datetime import datetime

from src.chatbot.repositories import ConversacionRepository, MensajeRepository
from src.chatbot.models import Conversacion, Mensaje, RoleMensaje, TipoPrompt
from src.chatbot.prompts import (
    # Diagnostic
    DIAGNOSTIC_SYSTEM_PROMPT,
    build_diagnostic_prompt,
    build_quick_diagnostic_prompt,
    # Maintenance
    MAINTENANCE_SYSTEM_PROMPT,
    build_maintenance_recommendation_prompt,
    # Explanation
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt,
    # ML Analysis (NEW v2.3)
    ML_ANALYSIS_SYSTEM_PROMPT,
    build_ml_analysis_report_prompt,
    build_quick_ml_summary_prompt,
    # Trip Analysis (NEW v2.3)
    TRIP_ANALYSIS_SYSTEM_PROMPT,
    build_trip_summary_prompt,
    # Sensor Reading (NEW v2.3)
    SENSOR_READING_SYSTEM_PROMPT,
    build_sensor_reading_prompt,
    build_multi_sensor_dashboard_prompt,
    # Freemium (NEW v2.3)
    FREEMIUM_COMPARISON_SYSTEM_PROMPT,
    build_plan_comparison_prompt,
    build_limit_reached_prompt,
    # Title generation
    generate_conversation_title,
)
from src.integraciones.llm_provider import get_llm_provider
from src.chatbot import validators


# Constantes de error
ERROR_CONVERSATION_ID_INVALID = "El formato del conversation_id es inválido"
ERROR_NO_ACCESS = "No tienes acceso a esta conversación"
ERROR_CONVERSATION_NOT_FOUND = "Conversación {} no encontrada"

# Constantes del sistema
DEFAULT_BIKE_MODEL = "KTM 390 Duke 2024"


class ChatbotService:
    """
    Servicio principal para el chatbot con límites Freemium.
    
    Free: 5 conversaciones/mes
    Pro: Conversaciones ilimitadas
    """

    def __init__(
        self, 
        conversacion_repo: ConversacionRepository, 
        mensaje_repo: MensajeRepository
    ):
        self.conversacion_repo = conversacion_repo
        self.mensaje_repo = mensaje_repo
        self.llm_provider = get_llm_provider()

    async def create_conversacion(
        self,
        usuario_id: int,
        moto_id: int,
        titulo: Optional[str] = None
    ) -> Conversacion:
        """
        Crea una nueva conversación.
        
        Args:
            usuario_id: ID del usuario
            moto_id: ID de la moto (obligatorio en v2.3)
            titulo: Título opcional (se genera automáticamente si no se provee)
            
        Returns:
            Conversación creada
            
        Raises:
            ValueError: Si el título es inválido
        """
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:12]}"
        
        # Validar título si se proporciona manualmente
        if titulo and not validators.validate_conversation_title(titulo):
            raise ValueError("El título debe tener entre 1 y 200 caracteres")
        
        # Si no se proporciona título, se dejará None y se generará automáticamente
        # después del primer mensaje (cuando tengamos contexto real)
        conversacion = Conversacion(
            conversation_id=conversation_id,
            usuario_id=usuario_id,
            moto_id=moto_id,
            titulo=titulo,  # Puede ser None inicialmente
            activa=True,
            total_mensajes=0,
            ultima_actividad=datetime.now()
        )
        
        return await self.conversacion_repo.create(conversacion)

    async def get_or_create_conversacion(
        self,
        usuario_id: int,
        moto_id: int,
        conversation_id: Optional[str] = None,
        titulo: Optional[str] = None
    ) -> Conversacion:
        """
        Obtiene una conversación existente o crea una nueva.
        
        Args:
            usuario_id: ID del usuario
            moto_id: ID de la moto
            conversation_id: ID de conversación existente (opcional)
            titulo: Título para nueva conversación (opcional)
            
        Returns:
            Conversación existente o nueva
        """
        if conversation_id:
            conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
            if conversacion and conversacion.usuario_id == usuario_id:
                return conversacion
        
        # Crear nueva conversación
        return await self.create_conversacion(usuario_id, moto_id, titulo)

    async def add_user_message(
        self,
        conversacion_id: int,
        contenido: str
    ) -> Mensaje:
        """
        Agrega un mensaje del usuario a la conversación.
        
        Args:
            conversacion_id: ID de la conversación
            contenido: Contenido del mensaje
            
        Returns:
            Mensaje creado
            
        Raises:
            ValueError: Si el mensaje excede la longitud máxima
        """
        # Validar longitud del mensaje
        if not validators.validate_message_length(contenido):
            raise ValueError("El mensaje debe tener entre 1 y 2000 caracteres")
        
        mensaje = Mensaje(
            conversacion_id=conversacion_id,
            role=RoleMensaje.user.value,  # Fix: Use value string
            contenido=contenido
        )
        
        return await self.mensaje_repo.create(mensaje)

    async def add_assistant_message(
        self,
        conversacion_id: int,
        contenido: str,
        tipo_prompt: TipoPrompt = TipoPrompt.general,
        tokens_usados: int = 0,
        tiempo_respuesta_ms: int = 0,
        modelo_usado: str = "unknown"
    ) -> Mensaje:
        """
        Agrega un mensaje del asistente a la conversación.
        
        MVP v2.3 - Ahora incluye métricas de LLM.
        
        Args:
            conversacion_id: ID de la conversación
            contenido: Contenido del mensaje
            tipo_prompt: Tipo de prompt usado
            tokens_usados: Tokens generados por el LLM
            tiempo_respuesta_ms: Tiempo de respuesta en milisegundos
            modelo_usado: Modelo de LLM usado
            
        Returns:
            Mensaje creado con métricas
        """
        # Asegurar que tipo_prompt sea el valor string
        tipo_prompt_val = tipo_prompt.value if isinstance(tipo_prompt, TipoPrompt) else tipo_prompt

        mensaje = Mensaje(
            conversacion_id=conversacion_id,
            role=RoleMensaje.assistant.value,  # Fix: Use value string
            contenido=contenido,
            tipo_prompt=tipo_prompt_val,
            tokens_usados=tokens_usados,
            tiempo_respuesta_ms=tiempo_respuesta_ms,
            modelo_usado=modelo_usado
        )
        
        return await self.mensaje_repo.create(mensaje)

    async def process_message(
        self,
        conversacion: Conversacion,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tipo_prompt_override: Optional[TipoPrompt] = None
    ) -> tuple[str, Mensaje, Mensaje]:
        """
        Procesa un mensaje del usuario y genera respuesta del LLM.
        
        Args:
            conversacion: Conversación activa
            message: Mensaje del usuario
            context: Contexto adicional (sensores, fallas, etc.)
            tipo_prompt_override: Tipo de prompt a usar (si no se especifica, se detecta)
            
        Returns:
            Tuple con (respuesta_texto, mensaje_usuario, mensaje_asistente)
            
        Raises:
            ValueError: Si el contexto es inválido
        """
        import time
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] ChatbotService.process_message iniciado. Message: {message[:50]}...")
        start_time = time.time()
        # Validar contexto si se proporciona
        if context and not validators.validate_context_data(context):
            raise ValueError("El contexto proporcionado es inválido o excede el tamaño máximo (50KB)")
        
        # 1. Guardar mensaje del usuario
        mensaje_usuario = await self.add_user_message(
            conversacion_id=conversacion.id,
            contenido=message
        )
        
        # 2. Detectar tipo de prompt
        tipo_prompt = tipo_prompt_override or self._detect_prompt_type(message)
        
        # 3. Construir prompts
        system_prompt, user_prompt = await self._build_prompts(
            tipo_prompt=tipo_prompt,
            message=message,
            conversacion_id=conversacion.id,
            context=context or {}
        )
        
        # 4. Generar respuesta del LLM con métricas
        response, metrics = await self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=1000,  # MVP: límite fijo
            temperature=0.7,
            return_metrics=True
        )
        
        # 5. Guardar mensaje del asistente con métricas
        mensaje_asistente = await self.add_assistant_message(
            conversacion_id=conversacion.id,
            contenido=response,
            tipo_prompt=tipo_prompt,
            tokens_usados=metrics.get("tokens_usados", 0),
            tiempo_respuesta_ms=metrics.get("tiempo_respuesta_ms", 0),
            modelo_usado=metrics.get("modelo_usado", "unknown")
        )
        
        # 6. Actualizar conversación
        await self.conversacion_repo.actualizar_actividad(conversacion)
        
        # 7. Generar título automáticamente si es el primer mensaje
        if not conversacion.titulo or conversacion.titulo.startswith("Conversación"):
            titulo_generado = generate_conversation_title(
                user_message=message,
                assistant_response=response,
                tipo_prompt=tipo_prompt
            )
            conversacion.titulo = titulo_generado
            await self.conversacion_repo.update(conversacion)
        
        return response, mensaje_usuario, mensaje_asistente

    async def process_message_stream(
        self,
        conversacion: Conversacion,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        tipo_prompt_override: Optional[TipoPrompt] = None
    ) -> AsyncGenerator[str, None]:
        """
        Procesa un mensaje con streaming de respuesta.
        
        Args:
            conversacion: Conversación activa
            message: Mensaje del usuario
            context: Contexto adicional
            tipo_prompt_override: Tipo de prompt a usar
            
        Yields:
            Chunks de texto de la respuesta
            
        Raises:
            ValueError: Si el contexto es inválido
        """
        # Validar contexto si se proporciona
        if context and not validators.validate_context_data(context):
            raise ValueError("El contexto proporcionado es inválido o excede el tamaño máximo (50KB)")
        
        # 1. Guardar mensaje del usuario
        await self.add_user_message(
            conversacion_id=conversacion.id,
            contenido=message
        )
        
        # 2. Detectar tipo de prompt
        tipo_prompt = tipo_prompt_override or self._detect_prompt_type(message)
        
        # 3. Construir prompts
        system_prompt, user_prompt = await self._build_prompts(
            tipo_prompt=tipo_prompt,
            message=message,
            conversacion_id=conversacion.id,
            context=context or {}
        )
        
        # 4. Stream de respuesta con métricas
        response_chunks = []
        metrics = None
        
        async for chunk in self.llm_provider.generate_stream(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.7,
            return_metrics=True
        ):
            # El último elemento puede ser un dict con métricas
            if isinstance(chunk, dict):
                metrics = chunk  # Capturar métricas al final
            else:
                response_chunks.append(chunk)
                yield chunk
        
        # 5. Guardar respuesta completa con métricas
        full_response = "".join(response_chunks)
        await self.add_assistant_message(
            conversacion_id=conversacion.id,
            contenido=full_response,
            tipo_prompt=tipo_prompt,
            tokens_usados=metrics.get("tokens_usados", 0) if metrics else 0,
            tiempo_respuesta_ms=metrics.get("tiempo_respuesta_ms", 0) if metrics else 0,
            modelo_usado=metrics.get("modelo_usado", "unknown") if metrics else "unknown"
        )

        # 6. Actualizar conversación
        
        # 7. Generar título automáticamente si es el primer mensaje (streaming)
        if not conversacion.titulo:
            titulo_generado = generate_conversation_title(
                user_message=message,
                assistant_response=full_response,
                tipo_prompt=tipo_prompt
            )
            conversacion.titulo = titulo_generado
            await self.conversacion_repo.update(conversacion)

    def _detect_prompt_type(self, message: str) -> TipoPrompt:
        """
        Detecta el tipo de prompt basado en el mensaje del usuario.
        
        MVP v2.3 - Detección expandida para nuevos tipos de prompts.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tipo de prompt detectado
        """
        message_lower = message.lower()
        
        # Keywords para análisis ML (alta prioridad - muy específico)
        ml_keywords = [
            "análisis ml", "predicción", "machine learning", "probabilidad",
            "modelo predictivo", "score de componente", "riesgo de falla",
            "predicciones", "análisis predictivo", "shap"
        ]
        if any(keyword in message_lower for keyword in ml_keywords):
            return TipoPrompt.ml_analysis
        
        # Keywords para análisis de viajes
        trip_keywords = [
            "viaje", "ruta", "trayecto", "conducción", "estilo de manejo",
            "eficiencia de combustible", "consumo", "rpm promedio", "aceleración",
            "patrón de conducción", "kilometraje del viaje"
        ]
        if any(keyword in message_lower for keyword in trip_keywords):
            return TipoPrompt.trip_analysis
        
        # Keywords para sensores (lecturas en tiempo real)
        sensor_keywords = [
            "sensor", "lectura actual", "temperatura actual", "rpm ahora",
            "velocidad actual", "presión de aceite", "nivel de combustible",
            "estado del componente", "dashboard", "panel de instrumentos"
        ]
        if any(keyword in message_lower for keyword in sensor_keywords):
            return TipoPrompt.sensor_reading
        
        # Keywords para Freemium (comparativas y planes)
        freemium_keywords = [
            "plan free", "plan pro", "diferencia entre planes", "actualizar plan",
            "límite alcanzado", "características premium", "qué incluye pro",
            "precio", "suscripción", "upgrade", "funcionalidades"
        ]
        if any(keyword in message_lower for keyword in freemium_keywords):
            return TipoPrompt.freemium
        
        # Keywords para diagnóstico
        diagnostic_keywords = [
            "problema", "falla", "error", "ruido", "vibración", "olor",
            "humo", "temperatura alta", "sobrecalienta", "no arranca", "se apaga"
        ]
        if any(keyword in message_lower for keyword in diagnostic_keywords):
            return TipoPrompt.diagnostic
        
        # Keywords para mantenimiento
        maintenance_keywords = [
            "mantenimiento", "servicio", "cambio de", "aceite", "filtro",
            "pastillas", "freno", "cadena", "neumático", "revisión", "cuándo cambiar"
        ]
        if any(keyword in message_lower for keyword in maintenance_keywords):
            return TipoPrompt.maintenance
        
        # Keywords para explicación
        explanation_keywords = [
            "qué es", "cómo funciona", "para qué sirve", "explicar", "significa",
            "diferencia entre", "por qué", "qué significa"
        ]
        if any(keyword in message_lower for keyword in explanation_keywords):
            return TipoPrompt.explanation
        
        # Por defecto: general
        return TipoPrompt.general

    async def _build_prompts(
        self,
        tipo_prompt: TipoPrompt,
        message: str,
        conversacion_id: int,
        context: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Construye los prompts del sistema y usuario.
        
        MVP v2.3 - Soporta tipos básicos: DIAGNOSTIC, MAINTENANCE, EXPLANATION, GENERAL.
        Los nuevos tipos (ML_ANALYSIS, TRIP_ANALYSIS, SENSOR_READING, FREEMIUM) usan
        prompts pre-construidos que vienen en context["user_prompt"].
        
        Args:
            tipo_prompt: Tipo de prompt
            message: Mensaje del usuario
            conversacion_id: ID de la conversación
            context: Contexto adicional
            
        Returns:
            Tuple con (system_prompt, user_prompt)
        """
        # Obtener historial de mensajes previos (últimos 5 para contexto)
        mensajes_previos = await self.mensaje_repo.get_ultimos_mensajes(
            conversacion_id,
            limit=5
        )
        
        # Construir contexto de conversación
        conversation_context = ""
        if mensajes_previos:
            conversation_context = "\n".join([
                f"{m.role.value.upper()}: {m.contenido}"
                for m in mensajes_previos
            ])
        
        # Seleccionar system prompt y construir user prompt según tipo
        if tipo_prompt == TipoPrompt.diagnostic:
            system_prompt = DIAGNOSTIC_SYSTEM_PROMPT
            if context.get("datos_sensores"):
                user_prompt = build_diagnostic_prompt(
                    sintomas=message,
                    datos_sensores=context.get("datos_sensores", {}),
                    fallas_recientes=context.get("fallas_recientes", []),
                    kilometraje=context.get("kilometraje", 0),
                    modelo_moto=context.get("modelo_moto", DEFAULT_BIKE_MODEL)
                )
            else:
                user_prompt = build_quick_diagnostic_prompt(message)
        
        elif tipo_prompt == TipoPrompt.maintenance:
            system_prompt = MAINTENANCE_SYSTEM_PROMPT
            if context.get("kilometraje_actual"):
                user_prompt = build_maintenance_recommendation_prompt(
                    kilometraje_actual=context.get("kilometraje_actual", 0),
                    ultimo_mantenimiento=context.get("ultimo_mantenimiento", {}),
                    mantenimientos_vencidos=context.get("mantenimientos_vencidos", []),
                    historial_fallas=context.get("historial_fallas", []),
                    patron_uso=context.get("patron_uso", {})
                )
            else:
                user_prompt = f"Pregunta de mantenimiento: {message}"
        
        elif tipo_prompt == TipoPrompt.explanation:
            system_prompt = EXPLANATION_SYSTEM_PROMPT
            user_prompt = build_explanation_prompt(
                pregunta=message,
                contexto_usuario=context
            )
        
        elif tipo_prompt == TipoPrompt.ml_analysis:
            system_prompt = ML_ANALYSIS_SYSTEM_PROMPT
            # Determinar si es análisis rápido o completo
            if context.get("quick_summary"):
                user_prompt = build_quick_ml_summary_prompt(
                    score_general=context.get("score_general", 0),
                    num_componentes_criticos=context.get("num_componentes_criticos", 0),
                    num_predicciones=context.get("num_predicciones", 0),
                    modelo_moto=context.get("modelo_moto", DEFAULT_BIKE_MODEL)
                )
            else:
                user_prompt = build_ml_analysis_report_prompt(
                    analysis_results=context.get("analysis_results", {}),
                    componentes_estado=context.get("componentes_estado", []),
                    predicciones=context.get("predicciones", []),
                    anomalias=context.get("anomalias", []),
                    kilometraje=context.get("kilometraje", 0),
                    modelo_moto=context.get("modelo_moto", DEFAULT_BIKE_MODEL),
                    es_usuario_pro=context.get("es_usuario_pro", False)
                )
        
        elif tipo_prompt == TipoPrompt.trip_analysis:
            system_prompt = TRIP_ANALYSIS_SYSTEM_PROMPT
            user_prompt = build_trip_summary_prompt(
                viaje=context.get("viaje", {}),
                telemetria=context.get("telemetria", {}),
                impacto_componentes=context.get("impacto_componentes", []),
                es_usuario_pro=context.get("es_usuario_pro", False)
            )
        
        elif tipo_prompt == TipoPrompt.sensor_reading:
            system_prompt = SENSOR_READING_SYSTEM_PROMPT
            # Determinar si es dashboard completo o sensor individual
            if context.get("dashboard"):
                user_prompt = build_multi_sensor_dashboard_prompt(
                    lecturas_actuales=context.get("lecturas_actuales", []),
                    alertas_activas=context.get("alertas_activas", []),
                    modelo_moto=context.get("modelo_moto", DEFAULT_BIKE_MODEL),
                    ultimo_analisis_ml=context.get("ultimo_analisis_ml", {})
                )
            else:
                user_prompt = build_sensor_reading_prompt(
                    sensor_tipo=context.get("sensor_tipo", "temperatura"),
                    valor_actual=context.get("valor_actual", 0.0),
                    unidad=context.get("unidad", "°C"),
                    estado_calculado=context.get("estado_calculado", "BUENO"),
                    reglas_estado=context.get("reglas_estado", {}),
                    historial_reciente=context.get("historial_reciente", []),
                    componente_nombre=context.get("componente_nombre", "Motor")
                )
        
        elif tipo_prompt == TipoPrompt.freemium:
            system_prompt = FREEMIUM_COMPARISON_SYSTEM_PROMPT
            # Determinar si es límite alcanzado o comparación de planes
            if context.get("limite_alcanzado"):
                user_prompt = build_limit_reached_prompt(
                    caracteristica=context.get("caracteristica", "Conversaciones"),
                    limite=context.get("limite", 5),
                    plan_actual=context.get("plan_actual", "free"),
                    contexto_uso=context.get("contexto_uso", {})
                )
            else:
                user_prompt = build_plan_comparison_prompt(
                    consulta_usuario=message,
                    plan_actual=context.get("plan_actual", "free"),
                    uso_actual=context.get("uso_actual", {}),
                    features_bloqueadas=context.get("features_bloqueadas", [])
                )
        
        else:  # TipoPrompt.GENERAL
            system_prompt = """Eres un asistente experto en motocicletas del sistema RIM- (Ride Intelligence Monitor).
Ayudas a los usuarios con información sobre sus motocicletas, mantenimiento, problemas técnicos y mejores prácticas.
Responde de forma clara, profesional y útil. Si no conoces la respuesta, admítelo y sugiere consultar con un mecánico."""
            user_prompt = message
        
        # Agregar contexto de conversación si existe
        if conversation_context:
            user_prompt = f"""CONTEXTO DE CONVERSACIÓN PREVIA:
{conversation_context}

MENSAJE ACTUAL DEL USUARIO:
{user_prompt}"""
        
        # Agregar contexto de moto si está disponible
        if context.get('moto_data'):
            from src.chatbot.formatters import format_moto_context_for_llm, format_user_plan_note
            
            # Formatear datos de la moto para el LLM
            moto_context_text = format_moto_context_for_llm(context['moto_data'])
            
            # Agregar al system prompt
            system_prompt += f"\n\n{moto_context_text}"
            
            # Agregar nota sobre el plan del usuario
            user_plan = context['moto_data'].get('user_plan', 'free')
            plan_note = format_user_plan_note(user_plan)
            system_prompt += plan_note
        
        return system_prompt, user_prompt

    async def get_conversacion_with_messages(
        self,
        conversation_id: str,
        usuario_id: int,
        limit: int = 50
    ) -> tuple[Conversacion, List[Mensaje]]:
        """
        Obtiene una conversación con sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para validar acceso)
            limit: Límite de mensajes a obtener
            
        Returns:
            Tuple con (conversacion, mensajes)
            
        Raises:
            ValueError: Si el conversation_id es inválido o el usuario no tiene acceso
        """
        # Validar formato del conversation_id
        if not validators.validate_conversation_id(conversation_id):
            raise ValueError(ERROR_CONVERSATION_ID_INVALID)
        
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        
        if not conversacion:
            raise ValueError(ERROR_CONVERSATION_NOT_FOUND.format(conversation_id))
        
        # Validar acceso del usuario
        if not validators.can_delete_conversation(usuario_id, conversacion.usuario_id):
            raise ValueError(ERROR_NO_ACCESS)
        
        mensajes = await self.mensaje_repo.get_by_conversacion(
            conversacion.id,
            limit=limit
        )
        
        return conversacion, mensajes

    async def archivar_conversacion(
        self,
        conversation_id: str,
        usuario_id: int
    ) -> Conversacion:
        """
        Archiva una conversación (la marca como inactiva).
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para validar acceso)
            
        Returns:
            Conversación archivada
            
        Raises:
            ValueError: Si la conversación no existe o el usuario no tiene acceso
        """
        # Validar formato del conversation_id
        if not validators.validate_conversation_id(conversation_id):
            raise ValueError(ERROR_CONVERSATION_ID_INVALID)
        
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        
        if not conversacion:
            raise ValueError(ERROR_CONVERSATION_NOT_FOUND.format(conversation_id))
        
        # Validar acceso del usuario
        if not validators.can_archive_conversation(usuario_id, conversacion.usuario_id):
            raise ValueError(ERROR_NO_ACCESS)
        
        conversacion.activa = False
        return await self.conversacion_repo.update(conversacion)

    async def delete_conversacion(
        self,
        conversation_id: str,
        usuario_id: int
    ) -> None:
        """
        Elimina una conversación y todos sus mensajes.
        
        Args:
            conversation_id: ID de la conversación
            usuario_id: ID del usuario (para validar acceso)
            
        Raises:
            ValueError: Si la conversación no existe o el usuario no tiene acceso
        """
        # Validar formato del conversation_id
        if not validators.validate_conversation_id(conversation_id):
            raise ValueError(ERROR_CONVERSATION_ID_INVALID)
        
        conversacion = await self.conversacion_repo.get_by_conversation_id(conversation_id)
        
        if not conversacion:
            raise ValueError(ERROR_CONVERSATION_NOT_FOUND.format(conversation_id))
        
        # Validar acceso del usuario
        if not validators.can_delete_conversation(usuario_id, conversacion.usuario_id):
            raise ValueError(ERROR_NO_ACCESS)
        
        await self.conversacion_repo.delete(conversacion)

    async def get_conversacion_stats(
        self,
        usuario_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conversaciones del usuario.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con estadísticas
        """
        total = await self.conversacion_repo.count_by_usuario(usuario_id, solo_activas=False)
        activas = await self.conversacion_repo.count_by_usuario(usuario_id, solo_activas=True)
        
        return {
            "total_conversaciones": total,
            "conversaciones_activas": activas,
            "conversaciones_archivadas": total - activas
        }
