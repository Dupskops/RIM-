"""
Rutas FastAPI para gestión de suscripciones v2.3 Freemium.

Endpoints para:
- Listar planes disponibles (Free/Pro)
- Consultar suscripción actual
- Verificar límites de características
- Registrar uso de características
- Cambiar de plan (upgrade/downgrade)
- Cancelar suscripción
- Ver historial de uso
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException

from ..config.dependencies import get_db, get_current_user
from ..auth.models import Usuario
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.base_models import ApiResponse

from .schemas import (
    PlanReadSchema,
    SuscripcionReadSchema,
    LimiteCheckResponse,
    LimiteRegistroResponse,
    UsoHistorialResponse,
    CambiarPlanRequest,
)
from .use_cases import (
    ListPlanesUseCase,
    GetMySuscripcionUseCase,
    CheckLimiteUseCase,
    RegistrarUsoUseCase,
    GetHistorialUsoUseCase,
    CambiarPlanUseCase,
    CancelSuscripcionUseCase,
)
from .validators import validate_clave_caracteristica


router = APIRouter()


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get(
    "/planes",
    response_model=ApiResponse[List[PlanReadSchema]],
    summary="Listar planes disponibles",
    tags=["Suscripciones - Público"]
)
async def list_planes(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Lista todos los planes disponibles con sus características y límites.
    
    **Planes v2.3 Freemium:**
    - **FREE**: Plan gratuito ($0/mes)
        - 11 características básicas
        - Límites mensuales: CHATBOT (5), ML_PREDICTIONS (4), EXPORT_REPORTS (10)
        - Max motos: 2
    
    - **Pro**: Plan premium ($29.99/mes)
        - 15 características completas
        - Límites ampliados: CHATBOT (50), ML_PREDICTIONS (100), EXPORT_REPORTS (ilimitado)
        - Max motos: 5
    
    **Útil para:**
    - UI de comparación de planes
    - Página de pricing
    - Validación de límites
    
    **Respuesta:**
    ```json
    {
        "success": true,
        "data": [
            {
            "id": 1,
            "nombre_plan": "FREE",
            "precio": "0.00",
            "caracteristicas": [...]
            },
            {
            "id": 2,
            "nombre_plan": "Pro",
            "precio": "29.99",
            "caracteristicas": [...]
            }
        ]
    }
    ```
    """
    use_case = ListPlanesUseCase(db)
    planes = await use_case.execute()
    
    return ApiResponse(
        success=True,
        message="Planes disponibles obtenidos exitosamente",
        data=planes
    )


# ==================== ENDPOINTS AUTENTICADOS ====================

@router.get(
    "/mi-suscripcion",
    response_model=ApiResponse[SuscripcionReadSchema],
    summary="Obtener mi suscripción actual",
    tags=["Suscripciones - Usuario"]
)
async def get_my_suscripcion(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Obtiene la suscripción activa del usuario autenticado.
    
    **Incluye:**
    - Plan actual (Free/Pro)
    - Características disponibles con límites
    - Fechas de inicio/fin
    - Estado de la suscripción
    
    **Respuesta:**
    ```json
    {
        "success": true,
        "data": {
            "id": 1,
            "usuario_id": 123,
            "plan": {
            "nombre_plan": "FREE",
            "caracteristicas": [...]
            },
            "fecha_inicio": "2025-01-01T00:00:00",
            "estado_suscripcion": "activa"
        }
    }
    ```
    """
    use_case = GetMySuscripcionUseCase(db)
    suscripcion = await use_case.execute(usuario_id=int(current_user.id))
    
    if not suscripcion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes una suscripción activa. Contacta con soporte."
        )
    
    return ApiResponse(
        success=True,
        message="Suscripción activa obtenida",
        data=suscripcion
    )


@router.get(
    "/limites/{caracteristica}",
    response_model=ApiResponse[LimiteCheckResponse],
    summary="Verificar límite de característica",
    tags=["Suscripciones - Límites"]
)
async def check_limite(
    caracteristica: str,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Verifica si el usuario puede usar una característica específica.
    
    **Características válidas:**
    - `CHATBOT`: Consultas al chatbot IA
    - `ML_PREDICTIONS`: Predicciones de fallos ML
    - `EXPORT_REPORTS`: Exportar reportes
    - `CUSTOM_ALERTS`: Alertas personalizadas
    - `MULTI_BIKE`: Número de motos registradas
    - Y más...
    
    **Lógica:**
    - Si `limite` es `null` = ilimitado (puede usar)
    - Si `limite` es `0` = bloqueado (no puede usar)
    - Si `usos_realizados >= limite` = límite alcanzado
    - Reinicio automático cada mes (periodo_mes)
    
    **Ejemplo - Límite NO alcanzado:**
    ```json
    {
        "puede_usar": true,
        "usos_realizados": 3,
        "limite": 5,
        "usos_restantes": 2,
        "mensaje": "Disponible: 2/5 usos restantes",
        "periodo_actual": "2025-11-01"
    }
    ```
    
    **Ejemplo - Límite ALCANZADO:**
    ```json
    {
        "puede_usar": false,
        "usos_realizados": 5,
        "limite": 5,
        "usos_restantes": 0,
        "mensaje": "Límite alcanzado (5/5). Resetea: 2025-12-01",
        "periodo_actual": "2025-11-01"
    }
    ```
    """
    # Validar característica
    valido, error = validate_clave_caracteristica(caracteristica)
    if not valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    use_case = CheckLimiteUseCase(db)
    result = await use_case.execute(
        usuario_id=int(current_user.id),
        clave_caracteristica=caracteristica.upper()
    )
    
    return ApiResponse(
        success=True,
        message="Límite verificado",
        data=result
    )


@router.post(
    "/limites/{caracteristica}/uso",
    response_model=ApiResponse[LimiteRegistroResponse],
    summary="Registrar uso de característica",
    tags=["Suscripciones - Límites"],
    status_code=status.HTTP_201_CREATED
)
async def registrar_uso(
    caracteristica: str,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Registra un uso de la característica y actualiza el contador mensual.
    
    **Flujo:**
    1. Verifica que el usuario pueda usar la característica
    2. Incrementa el contador de usos del mes
    3. Retorna estado actualizado
    
    **Validaciones automáticas:**
    - ❌ Si límite alcanzado → HTTP 403
    - ❌ Si característica bloqueada (limite=0) → HTTP 403
    - ✅ Si puede usar → incrementa contador y retorna 201
    
    **Uso típico:**
    ```python
    # Antes de ejecutar una acción limitada:
    POST /api/suscripciones/limites/CHATBOT/uso
    
    # Si exitoso (201):
    → Ejecutar acción (enviar mensaje al chatbot)
    
    # Si falla (403):
    → Mostrar mensaje "Límite alcanzado, upgrade a Pro"
    ```
    
    **Respuesta exitosa:**
    ```json
    {
        "exito": true,
        "usos_realizados": 4,
        "limite": 5,
        "usos_restantes": 1,
        "mensaje": "Uso registrado. Restantes: 1/5"
    }
    ```
    
    **Respuesta límite alcanzado (403):**
    ```json
    {
        "detail": "Límite alcanzado (5/5). Upgrade a Pro para más usos."
    }
    ```
    """
    # Validar característica
    valido, error = validate_clave_caracteristica(caracteristica)
    if not valido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    use_case = RegistrarUsoUseCase(db)
    
    try:
        result = await use_case.execute(
            usuario_id=int(current_user.id),
            clave_caracteristica=caracteristica.upper()
        )
    except ValueError as e:
        # Límite alcanzado o característica bloqueada
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    if not result.exito:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.mensaje
        )
    
    return ApiResponse(
        success=True,
        message="Uso registrado exitosamente",
        data=result
    )


@router.get(
    "/limites/historial",
    response_model=ApiResponse[List[UsoHistorialResponse]],
    summary="Ver historial de uso del mes",
    tags=["Suscripciones - Límites"]
)
async def get_historial_uso(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Obtiene el historial de uso de características del mes actual.
    
    **Muestra:**
    - Todas las características usadas este mes
    - Contador de usos por característica
    - Límite mensual de cada una
    - Último uso registrado
    
    **Útil para:**
    - Dashboard de uso
    - Página "Mi cuenta"
    - Gráficas de consumo
    
    **Respuesta:**
    ```json
    {
        "success": true,
        "data": [
            {
            "caracteristica": "CHATBOT",
            "usos_realizados": 3,
            "limite_mensual": 5,
            "ultimo_uso_at": "2025-11-15T10:30:00",
            "periodo_mes": "2025-11-01"
            },
            {
            "caracteristica": "ML_PREDICTIONS",
            "usos_realizados": 2,
            "limite_mensual": 4,
            "ultimo_uso_at": "2025-11-14T15:20:00",
            "periodo_mes": "2025-11-01"
            }
        ]
    }
    ```
    """
    use_case = GetHistorialUsoUseCase(db)
    historial = await use_case.execute(usuario_id=int(current_user.id))
    
    return ApiResponse(
        success=True,
        message=f"Historial de uso obtenido ({len(historial)} características)",
        data=historial
    )


@router.post(
    "/cambiar-plan",
    response_model=ApiResponse[SuscripcionReadSchema],
    summary="Cambiar de plan (upgrade/downgrade)",
    tags=["Suscripciones - Gestión"]
)
async def cambiar_plan(
    request: CambiarPlanRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Cambia el plan del usuario (genérico para cualquier cambio).
    
    **Casos de uso:**
    - Free → Pro (upgrade)
    - Pro → Free (downgrade)
    - Cualquier plan futuro
    
    **Validaciones:**
    - ✅ plan_id debe existir en BD
    - ✅ Usuario debe tener suscripción activa
    - ⚠️ No validamos cambio al mismo plan (es idempotente)
    
    **Request:**
    ```json
    {
      "plan_id": 2  // ID del plan Pro
    }
    ```
    
    **Respuesta:**
    ```json
    {
        "success": true,
        "message": "Plan cambiado exitosamente de FREE a Pro",
        "data": {
            "id": 1,
            "usuario_id": 123,
            "plan": {
            "nombre_plan": "Pro",
            "precio": "29.99",
            "caracteristicas": [...]
            }
        }
    }
    ```
    
    **Nota:** En v2.3 Freemium no hay sistema de pagos. El cambio es inmediato.
    En producción, upgrade a Pro requeriría validar pago primero.
    """
    use_case = CambiarPlanUseCase(db)
    
    try:
        suscripcion = await use_case.execute(
            usuario_id=int(current_user.id),
            nuevo_plan_id=request.plan_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return ApiResponse(
        success=True,
        message=f"Plan cambiado exitosamente",
        data=suscripcion
    )


@router.post(
    "/cancelar",
    response_model=ApiResponse[SuscripcionReadSchema],
    summary="Cancelar suscripción (downgrade a Free)",
    tags=["Suscripciones - Gestión"]
)
async def cancel_suscripcion(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Cancela la suscripción Pro del usuario (downgrade a Free).
    
    **Comportamiento:**
    - Si usuario tiene plan Pro → downgrade inmediato a Free
    - Si usuario ya tiene plan Free → error (nada que cancelar)
    
    **Lógica v2.3:**
    - Cancelación siempre es inmediata
    - No hay periodo de gracia ni reembolsos
    - Límites se ajustan automáticamente a Free
    
    **Respuesta exitosa:**
    ```json
    {
        "success": true,
        "message": "Suscripción Pro cancelada. Downgrade a FREE completado",
        "data": {
            "plan": {
            "nombre_plan": "FREE"
            }
        }
    }
    ```
    
    **Error - ya en Free (400):**
    ```json
    {
        "detail": "No puedes cancelar el plan FREE. Ya tienes el plan base gratuito."
    }
    ```
    """
    use_case = CancelSuscripcionUseCase(db)
    
    try:
        suscripcion = await use_case.execute(usuario_id=int(current_user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return ApiResponse(
        success=True,
        message="Suscripción cancelada exitosamente. Downgrade a FREE completado",
        data=suscripcion
    )

