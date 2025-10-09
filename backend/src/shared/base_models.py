"""
Modelos base para peticiones y respuestas de la API.
Proporciona estructuras genéricas y reutilizables para estandarizar la comunicación.
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# TYPE VARIABLES PARA GENÉRICOS
# ============================================
T = TypeVar('T')  # Tipo genérico para datos


# ============================================
# MODELOS BASE DE RESPUESTA
# ============================================

class ApiResponse(BaseModel, Generic[T]):
    """
    Respuesta genérica de la API.
    
    Uso:
        @router.get("/users/{id}", response_model=ApiResponse[UserResponse])
        async def get_user(id: int):
            user = await get_user_by_id(id)
            return ApiResponse(
                success=True,
                message="Usuario encontrado",
                data=user
            )
    
    Attributes:
        success: Indica si la operación fue exitosa
        message: Mensaje descriptivo de la operación
        data: Datos de la respuesta (tipados según T)
        timestamp: Momento en que se generó la respuesta
        version: Versión de la API
    """
    success: bool = Field(
        ..., 
        description="Indica si la operación fue exitosa"
    )
    message: str = Field(
        ..., 
        description="Mensaje descriptivo de la operación",
        examples=["Operación exitosa", "Usuario creado correctamente"]
    )
    data: Optional[T] = Field(
        None, 
        description="Datos de la respuesta"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento en que se generó la respuesta"
    )
    version: str = Field(
        default="1.0.0",
        description="Versión de la API"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación exitosa",
                "data": {"id": 1, "name": "Ejemplo"},
                "timestamp": "2025-10-08T10:30:00Z",
                "version": "1.0.0"
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """
    Respuesta de éxito simplificada (sin timestamp/version).
    
    Uso para operaciones rápidas donde no se necesita metadata extra.
    
    Attributes:
        success: Siempre True
        message: Mensaje de éxito
        data: Datos opcionales
    """
    success: bool = Field(
        default=True,
        description="Siempre True en respuestas exitosas"
    )
    message: str = Field(
        ...,
        description="Mensaje de éxito",
        examples=["Creado exitosamente", "Actualizado correctamente"]
    )
    data: Optional[T] = Field(
        None,
        description="Datos opcionales de la respuesta"
    )


class ErrorDetail(BaseModel):
    """
    Detalle de un error específico.
    
    Útil para validaciones que fallan en múltiples campos.
    
    Attributes:
        field: Campo que causó el error (opcional)
        message: Mensaje descriptivo del error
        code: Código de error específico (opcional)
    """
    field: Optional[str] = Field(
        None,
        description="Campo que causó el error",
        examples=["email", "password", "moto_id"]
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo del error",
        examples=["Email inválido", "Campo requerido"]
    )
    code: Optional[str] = Field(
        None,
        description="Código de error específico",
        examples=["INVALID_EMAIL", "REQUIRED_FIELD", "OUT_OF_RANGE"]
    )


class ErrorResponse(BaseModel):
    """
    Respuesta estandarizada de error.
    
    Uso:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                success=False,
                error="Validación fallida",
                message="El email es inválido",
                details=[
                    ErrorDetail(field="email", message="Formato inválido", code="INVALID_EMAIL")
                ]
            ).model_dump()
        )
    
    Attributes:
        success: Siempre False en errores
        error: Tipo/categoría del error
        message: Mensaje principal del error
        details: Lista de detalles específicos del error
        timestamp: Momento del error
        path: Path del endpoint que falló (opcional)
        request_id: ID de request para tracking (opcional)
    """
    success: bool = Field(
        default=False,
        description="Siempre False en errores"
    )
    error: str = Field(
        ...,
        description="Tipo o categoría del error",
        examples=["ValidationError", "AuthenticationError", "NotFoundError"]
    )
    message: str = Field(
        ...,
        description="Mensaje principal del error",
        examples=["Usuario no encontrado", "Credenciales inválidas"]
    )
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Lista de detalles específicos del error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento en que ocurrió el error"
    )
    path: Optional[str] = Field(
        None,
        description="Path del endpoint que falló",
        examples=["/api/auth/login", "/api/motos/123"]
    )
    request_id: Optional[str] = Field(
        None,
        description="ID de request para tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "Error de validación en los datos",
                "details": [
                    {
                        "field": "email",
                        "message": "Email inválido",
                        "code": "INVALID_EMAIL"
                    }
                ],
                "timestamp": "2025-10-08T10:30:00Z",
                "path": "/api/auth/register"
            }
        }


class PaginationMeta(BaseModel):
    """
    Metadata de paginación.
    
    Attributes:
        page: Página actual (1-indexed)
        per_page: Items por página
        total_items: Total de items en toda la colección
        total_pages: Total de páginas
        has_next: Si hay página siguiente
        has_prev: Si hay página anterior
        next_page: Número de la página siguiente (None si no hay)
        prev_page: Número de la página anterior (None si no hay)
    """
    page: int = Field(
        ...,
        ge=1,
        description="Página actual (1-indexed)",
        examples=[1, 2, 3]
    )
    per_page: int = Field(
        ...,
        ge=1,
        le=100,
        description="Items por página",
        examples=[10, 20, 50]
    )
    total_items: int = Field(
        ...,
        ge=0,
        description="Total de items en toda la colección"
    )
    total_pages: int = Field(
        ...,
        ge=0,
        description="Total de páginas"
    )
    has_next: bool = Field(
        ...,
        description="Si hay página siguiente"
    )
    has_prev: bool = Field(
        ...,
        description="Si hay página anterior"
    )
    next_page: Optional[int] = Field(
        None,
        description="Número de la página siguiente"
    )
    prev_page: Optional[int] = Field(
        None,
        description="Número de la página anterior"
    )

    @classmethod
    def create(cls, page: int, per_page: int, total_items: int) -> "PaginationMeta":
        """
        Factory method para crear metadata de paginación.
        
        Args:
            page: Página actual
            per_page: Items por página
            total_items: Total de items
        
        Returns:
            PaginationMeta con todos los campos calculados
        """
        total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        return cls(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=page + 1 if has_next else None,
            prev_page=page - 1 if has_prev else None
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Respuesta paginada genérica.
    
    Uso:
        @router.get("/users", response_model=PaginatedResponse[UserResponse])
        async def list_users(page: int = 1, per_page: int = 20):
            users, total = await get_users_paginated(page, per_page)
            return PaginatedResponse(
                success=True,
                message="Usuarios obtenidos",
                data=users,
                pagination=PaginationMeta.create(page, per_page, total)
            )
    
    Attributes:
        success: Si la operación fue exitosa
        message: Mensaje descriptivo
        data: Lista de items (tipados según T)
        pagination: Metadata de paginación
        timestamp: Momento de la respuesta
    """
    success: bool = Field(
        default=True,
        description="Si la operación fue exitosa"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo",
        examples=["Datos obtenidos correctamente", "Lista de usuarios"]
    )
    data: List[T] = Field(
        ...,
        description="Lista de items paginados"
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Metadata de paginación"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento de la respuesta"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Usuarios obtenidos",
                "data": [
                    {"id": 1, "name": "Usuario 1"},
                    {"id": 2, "name": "Usuario 2"}
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False,
                    "next_page": 2,
                    "prev_page": None
                },
                "timestamp": "2025-10-08T10:30:00Z"
            }
        }


class ListResponse(BaseModel, Generic[T]):
    """
    Respuesta simple con lista de items (sin paginación).
    
    Uso para listas pequeñas donde no se necesita paginación.
    
    Attributes:
        success: Si la operación fue exitosa
        message: Mensaje descriptivo
        data: Lista de items
        count: Número de items en la lista
    """
    success: bool = Field(
        default=True,
        description="Si la operación fue exitosa"
    )
    message: str = Field(
        ...,
        description="Mensaje descriptivo"
    )
    data: List[T] = Field(
        ...,
        description="Lista de items"
    )
    count: int = Field(
        ...,
        ge=0,
        description="Número de items en la lista"
    )

    @classmethod
    def create(cls, message: str, data: List[T]) -> "ListResponse[T]":
        """
        Factory method para crear respuesta de lista.
        
        Args:
            message: Mensaje descriptivo
            data: Lista de items
        
        Returns:
            ListResponse con count calculado automáticamente
        """
        return cls(
            message=message,
            data=data,
            count=len(data)
        )


# ============================================
# MODELOS BASE DE REQUEST
# ============================================

class PaginationParams(BaseModel):
    """
    Parámetros comunes de paginación para peticiones.
    
    Uso:
        @router.get("/users")
        async def list_users(pagination: PaginationParams = Depends()):
            users = await get_users(pagination.page, pagination.per_page)
            ...
    
    Attributes:
        page: Número de página (default: 1)
        per_page: Items por página (default: 20, max: 100)
    """
    page: int = Field(
        default=1,
        ge=1,
        description="Número de página (1-indexed)",
        examples=[1, 2, 3]
    )
    per_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items por página (máximo 100)",
        examples=[10, 20, 50]
    )

    @property
    def offset(self) -> int:
        """Calcula el offset para la query de DB."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Retorna el límite (per_page)."""
        return self.per_page


class SortParams(BaseModel):
    """
    Parámetros de ordenamiento.
    
    Attributes:
        sort_by: Campo por el cual ordenar
        sort_order: Orden ascendente (asc) o descendente (desc)
    """
    sort_by: Optional[str] = Field(
        None,
        description="Campo por el cual ordenar",
        examples=["created_at", "name", "price"]
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Orden: 'asc' (ascendente) o 'desc' (descendente)"
    )


class FilterParams(BaseModel):
    """
    Parámetros base de filtrado.
    
    Heredar de esta clase para agregar filtros específicos.
    
    Attributes:
        search: Búsqueda de texto general
        created_after: Filtrar por fecha de creación (después de)
        created_before: Filtrar por fecha de creación (antes de)
    """
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Búsqueda de texto general"
    )
    created_after: Optional[datetime] = Field(
        None,
        description="Filtrar registros creados después de esta fecha"
    )
    created_before: Optional[datetime] = Field(
        None,
        description="Filtrar registros creados antes de esta fecha"
    )


# ============================================
# UTILIDADES
# ============================================

def create_success_response(
    message: str,
    data: Optional[Any] = None
) -> dict:
    """
    Helper para crear respuestas de éxito rápidamente.
    
    Args:
        message: Mensaje de éxito
        data: Datos opcionales
    
    Returns:
        Diccionario con formato ApiResponse
    """
    return ApiResponse(
        success=True,
        message=message,
        data=data
    ).model_dump()


def create_error_response(
    error: str,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    path: Optional[str] = None
) -> dict:
    """
    Helper para crear respuestas de error rápidamente.
    
    Args:
        error: Tipo de error
        message: Mensaje del error
        details: Detalles opcionales
        path: Path del endpoint
    
    Returns:
        Diccionario con formato ErrorResponse
    """
    return ErrorResponse(
        error=error,
        message=message,
        details=details,
        path=path
    ).model_dump()


def create_paginated_response(
    message: str,
    data: List[Any],
    page: int,
    per_page: int,
    total_items: int
) -> dict:
    """
    Helper para crear respuestas paginadas rápidamente.
    
    Args:
        message: Mensaje descriptivo
        data: Lista de items
        page: Página actual
        per_page: Items por página
        total_items: Total de items
    
    Returns:
        Diccionario con formato PaginatedResponse
    """
    return PaginatedResponse(
        message=message,
        data=data,
        pagination=PaginationMeta.create(page, per_page, total_items)
    ).model_dump()
