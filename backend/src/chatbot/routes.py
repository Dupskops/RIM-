"""
Rutas REST API para el chatbot.
"""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.dependencies import get_current_user
from src.usuarios.models import Usuario
from src.chatbot import schemas, use_cases
from src.shared.base_models import (
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    PaginationParams,
    PaginationMeta
)


router = APIRouter()


@router.post("/", response_model=ApiResponse[schemas.ConversacionResponse], status_code=201)
async def create_conversacion(
    data: schemas.ConversacionCreate,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> ApiResponse[schemas.ConversacionResponse]:
    """
    Crea una nueva conversación.
    
    - **titulo**: Título de la conversación
    - **moto_id**: ID de la moto asociada (opcional)
    """
    use_case = use_cases.CreateConversacionUseCase(session)
    
    conversacion = await use_case.execute(
        usuario_id=current_user.id,
        moto_id=data.moto_id,
        titulo=data.titulo
    )
    
    return ApiResponse(
        success=True,
        message="Conversación creada exitosamente",
        data=schemas.ConversacionResponse.model_validate(conversacion)
    )


@router.post("/chat", response_model=ApiResponse[schemas.ChatResponse])
async def send_message(
    data: schemas.ChatRequest,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> ApiResponse[schemas.ChatResponse]:
    """
    Envía un mensaje al chatbot.
    
    - **message**: Mensaje del usuario
    - **conversation_id**: ID de conversación existente (opcional)
    - **moto_id**: ID de la moto para contexto (opcional)
    - **tipo_prompt**: Tipo de prompt (diagnostic/maintenance/explanation/general)
    - **context**: Contexto adicional (sensores, fallas, etc.)
    - **stream**: Si True, retorna streaming (usar SSE)
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    start_time = time.time()
    logger.info(f"[DEBUG] Recibida petición POST /chat. Message len: {len(data.message)}")

    # Si se solicita streaming, usar endpoint de streaming
    if data.stream:
        raise HTTPException(
            status_code=400,
            detail="Para streaming, usar el endpoint /chat-stream o WebSocket"
        )
    
    use_case = use_cases.SendMessageUseCase(session)
    
    # Convertir tipo_prompt de string a enum si se proporciona
    tipo_prompt_enum = None
    if data.tipo_prompt:
        try:
            from src.chatbot.models import TipoPrompt
            tipo_prompt_enum = TipoPrompt(data.tipo_prompt.lower())
        except (ValueError, AttributeError):
            pass  # Si no es válido, se detectará automáticamente
    
    # Cargar contexto de moto automáticamente si moto_id está presente
    context = data.context or {}
    if data.moto_id:
        try:
            from src.chatbot.context_builder import build_moto_context
            
            # Construir contexto de la moto según el plan del usuario
            moto_context = await build_moto_context(
                moto_id=data.moto_id,
                user_id=current_user.id,
                db=session
            )
            
            # Agregar al contexto
            context['moto_data'] = moto_context
            logger.info(f"[DEBUG] Contexto de moto cargado. Plan: {moto_context.get('user_plan')}")
        except Exception as e:
            # Si falla la carga de contexto, continuar sin él
            logger.warning(f"Error cargando contexto de moto: {e}")
    
    try:
        response, conversacion, mensaje_usuario, mensaje_asistente = await use_case.execute(
            usuario_id=current_user.id,
            message=data.message,
            moto_id=data.moto_id,
            conversation_id=data.conversation_id,
            tipo_prompt=tipo_prompt_enum,
            context=context
        )
        
        chat_response = schemas.ChatResponse(
            message=response,
            conversation_id=conversacion.conversation_id,
            mensaje_usuario_id=mensaje_usuario.id,
            mensaje_asistente_id=mensaje_asistente.id,
            tipo_prompt=mensaje_asistente.tipo_prompt
        )
        
        return ApiResponse(
            success=True,
            message="Mensaje procesado exitosamente",
            data=chat_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")


@router.post("/chat-stream")
async def send_message_stream(
    data: schemas.ChatRequest,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Envía mensaje con streaming de respuesta (Server-Sent Events).
    
    Retorna chunks de texto en tiempo real.
    """
    use_case = use_cases.SendMessageStreamUseCase(session)
    
    # Convertir tipo_prompt de string a enum si se proporciona
    tipo_prompt_enum = None
    if data.tipo_prompt:
        try:
            from src.chatbot.models import TipoPrompt
            tipo_prompt_enum = TipoPrompt(data.tipo_prompt.lower())
        except (ValueError, AttributeError):
            pass  # Si no es válido, se detectará automáticamente
    
    async def event_generator():
        """Genera eventos SSE."""
        try:
            async for chunk in use_case.execute(
                usuario_id=current_user.id,
                message=data.message,
                moto_id=data.moto_id,
                conversation_id=data.conversation_id,
                tipo_prompt=tipo_prompt_enum,
                context=data.context
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except ValueError as e:
            yield f"event: error\ndata: {str(e)}\n\n"
        except Exception:
            yield "event: error\ndata: Error procesando mensaje\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/{conversation_id}", response_model=ApiResponse[schemas.ConversacionWithMessagesResponse])
async def get_conversacion(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Límite de mensajes"),
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> ApiResponse[schemas.ConversacionWithMessagesResponse]:
    """
    Obtiene una conversación con sus mensajes.
    
    - **conversation_id**: ID de la conversación
    - **limit**: Cantidad máxima de mensajes a retornar (1-200)
    """
    use_case = use_cases.GetConversacionUseCase(session)
    
    try:
        conversacion, mensajes = await use_case.execute(
            conversation_id=conversation_id,
            usuario_id=current_user.id,
            limit=limit
        )
        
        return ApiResponse(
            success=True,
            message="Conversación obtenida exitosamente",
            data=schemas.ConversacionWithMessagesResponse(
                conversacion=schemas.ConversacionResponse.model_validate(conversacion),
                mensajes=[schemas.MensajeResponse.model_validate(m) for m in mensajes]
            )
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/usuario/{usuario_id}", response_model=PaginatedResponse[schemas.ConversacionResponse])
async def list_conversaciones(
    usuario_id: int,
    filters: Annotated[schemas.ConversacionFilterParams, Depends()],
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> PaginatedResponse[schemas.ConversacionResponse]:
    """
    Lista las conversaciones de un usuario.
    
    - **usuario_id**: ID del usuario
    - **solo_activas**: Filtrar solo activas
    - **skip**: Offset para paginación
    - **limit**: Límite de resultados (1-100)
    """
    # Verificar acceso (solo el usuario o admin)
    if current_user.id != usuario_id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes acceso a estas conversaciones")
    
    # Forzar usuario_id del path
    filters.usuario_id = usuario_id
    
    use_case = use_cases.ListConversacionesByUsuarioUseCase(session)
    
    conversaciones, total = await use_case.execute(
        filters=filters,
        pagination=pagination
    )
    
    return PaginatedResponse(
        success=True,
        message="Conversaciones obtenidas exitosamente",
        data=[schemas.ConversacionResponse.model_validate(c) for c in conversaciones],
        pagination=PaginationMeta.create(
            page=pagination.page,
            per_page=pagination.per_page,
            total_items=total
        )
    )

"""
@router.post("/messages/{mensaje_id}/feedback", response_model=ApiResponse[schemas.MensajeResponse])
async def add_feedback(
    mensaje_id: int,
    data: schemas.MensajeFeedback,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> ApiResponse[schemas.MensajeResponse]:
    
    Agrega feedback a un mensaje del asistente.
    
    - **mensaje_id**: ID del mensaje
    - **util**: Si la respuesta fue útil
    - **feedback**: Comentario adicional (opcional)
    
    use_case = use_cases.AddFeedbackUseCase(session)
    
    try:
        mensaje = await use_case.execute(
            mensaje_id=mensaje_id,
            usuario_id=current_user.id,
            util=data.util,
            feedback=data.feedback
        )
        
        return ApiResponse(
            success=True,
            message="Feedback agregado exitosamente",
            data=schemas.MensajeResponse.model_validate(mensaje)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
"""

@router.delete("/{conversation_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_conversacion(
    conversation_id: str,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """
    Elimina una conversación y sus mensajes.
    
    - **conversation_id**: ID de la conversación
    """
    use_case = use_cases.DeleteConversacionUseCase(session)
    
    try:
        await use_case.execute(
            conversation_id=conversation_id,
            usuario_id=current_user.id
        )
        return create_success_response(
            message="Conversación eliminada exitosamente",
            data=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{conversation_id}/history", response_model=SuccessResponse[None], status_code=200)
async def clear_history(
    conversation_id: int,
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> SuccessResponse[None]:
    """
    Limpia el historial de mensajes de una conversación.
    
    - **conversation_id**: ID de la conversación
    """
    use_case = use_cases.ClearHistoryUseCase(session)
    
    try:
        await use_case.execute(
            conversacion_id=conversation_id,
            usuario_id=current_user.id
        )
        return create_success_response(
            message="Historial limpiado exitosamente",
            data=None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats/summary", response_model=ApiResponse[schemas.ConversacionStatsResponse])
async def get_stats(
    usuario_id: Optional[int] = Query(None, description="ID del usuario (None para stats globales)"),
    current_user: Usuario = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> ApiResponse[schemas.ConversacionStatsResponse]:
    """
    Obtiene estadísticas del chatbot.
    
    - **usuario_id**: ID del usuario (None para estadísticas globales, solo admin)
    
    **Requiere nivel Premium para acceder.**
    """
    # Verificar acceso Premium
    if current_user.nivel_acceso != "premium":
        raise HTTPException(
            status_code=403,
            detail="Esta función requiere suscripción Premium"
        )
    
    # Si pide stats globales, verificar que sea admin
    if usuario_id is None and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Solo admin puede ver stats globales")
    
    # Si pide stats de otro usuario, verificar que sea admin
    if usuario_id and usuario_id != current_user.id and not current_user.es_admin:
        raise HTTPException(status_code=403, detail="No tienes acceso a estas estadísticas")
    
    use_case = use_cases.GetStatsUseCase(session)
    stats = await use_case.execute(usuario_id or current_user.id)
    
    return ApiResponse(
        success=True,
        message="Estadísticas obtenidas exitosamente",
        data=schemas.ConversacionStatsResponse(**stats)
    )
