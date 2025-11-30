"""
Schemas de validación para el módulo de notificaciones.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

from src.notificaciones.models import TipoNotificacion, CanalNotificacion, EstadoNotificacion
from src.shared.base_models import FilterParams


# ============================================
# REQUEST SCHEMAS
# ============================================

class NotificacionCreate(BaseModel):
    """Schema para crear una notificación."""
    usuario_id: int = Field(..., gt=0, description="ID del usuario destinatario")
    titulo: str = Field(..., min_length=1, max_length=200, description="Título de la notificación")
    mensaje: str = Field(..., min_length=1, description="Mensaje de la notificación")
    tipo: TipoNotificacion = Field(default=TipoNotificacion.INFO, description="Tipo de notificación")
    canal: CanalNotificacion = Field(default=CanalNotificacion.IN_APP, description="Canal de envío")
    
    referencia_tipo: Optional[str] = Field(default=None, max_length=50, description="Tipo de referencia")
    referencia_id: Optional[int] = Field(default=None, description="ID del objeto referenciado")


class NotificacionMasivaCreate(BaseModel):
    """Schema para crear notificaciones masivas."""
    usuarios_ids: list[int] = Field(..., min_length=1, description="Lista de IDs de usuarios")
    titulo: str = Field(..., min_length=1, max_length=200)
    mensaje: str = Field(..., min_length=1)
    tipo: TipoNotificacion = Field(default=TipoNotificacion.INFO)
    canal: CanalNotificacion = Field(default=CanalNotificacion.IN_APP)
    
    canal: CanalNotificacion = Field(default=CanalNotificacion.IN_APP)

class NotificacionFilterParams(FilterParams):
    """Parámetros de filtrado para notificaciones."""
    solo_no_leidas: Optional[bool] = Field(default=None, description="Filtrar solo no leídas")
    tipo: Optional[TipoNotificacion] = Field(default=None, description="Filtrar por tipo")
    canal: Optional[CanalNotificacion] = Field(default=None, description="Filtrar por canal")
    estado: Optional[EstadoNotificacion] = Field(default=None, description="Filtrar por estado")
    referencia_tipo: Optional[str] = Field(default=None, description="Filtrar por tipo de referencia")
    referencia_id: Optional[int] = Field(default=None, description="Filtrar por ID de referencia")


class MarcarLeidaRequest(BaseModel):
    """Schema para marcar notificaciones como leídas."""
    notificacion_ids: Optional[list[int]] = Field(default=None, description="IDs de notificaciones a marcar (None = todas)")


class PreferenciaNotificacionUpdate(BaseModel):
    """Schema para actualizar preferencias de notificaciones."""
    in_app_habilitado: Optional[bool] = None
    email_habilitado: Optional[bool] = None
    push_habilitado: Optional[bool] = None
    sms_habilitado: Optional[bool] = None
    
    notif_fallas_habilitado: Optional[bool] = None
    notif_mantenimiento_habilitado: Optional[bool] = None
    notif_sensores_habilitado: Optional[bool] = None
    notif_sistema_habilitado: Optional[bool] = None
    notif_marketing_habilitado: Optional[bool] = None
    
    no_molestar_inicio: Optional[str] = Field(default=None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    no_molestar_fin: Optional[str] = Field(default=None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    
    configuracion_adicional: Optional[dict[str, Any]] = None


# ============================================
# RESPONSE SCHEMAS
# ============================================

class NotificacionResponse(BaseModel):
    """Schema de respuesta para una notificación."""
    id: int
    usuario_id: int
    titulo: str
    mensaje: str
    tipo: TipoNotificacion
    canal: CanalNotificacion
    estado: EstadoNotificacion
    
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[int] = None
    
    leida: bool
    leida_en: Optional[datetime] = None
    
    enviada: bool
    enviada_en: Optional[datetime] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificacionStatsResponse(BaseModel):
    """Schema de respuesta para estadísticas de notificaciones."""
    total: int
    no_leidas: int
    leidas: int
    por_tipo: dict[str, int]
    por_canal: dict[str, int]
    por_estado: dict[str, int]


class PreferenciaNotificacionResponse(BaseModel):
    """Schema de respuesta para preferencias de notificaciones."""
    id: int
    usuario_id: int
    
    in_app_habilitado: bool
    email_habilitado: bool
    push_habilitado: bool
    sms_habilitado: bool
    
    notif_fallas_habilitado: bool
    notif_mantenimiento_habilitado: bool
    notif_sensores_habilitado: bool
    notif_sistema_habilitado: bool
    notif_marketing_habilitado: bool
    
    no_molestar_inicio: Optional[str] = None
    no_molestar_fin: Optional[str] = None
    
    configuracion_adicional: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificacionMasivaResponse(BaseModel):
    """Schema de respuesta para notificación masiva."""
    total_creadas: int
    notificaciones: list[NotificacionResponse]


# ============================================
# WEBSOCKET SCHEMAS
# ============================================

class WSNotificacionNueva(BaseModel):
    """Mensaje WebSocket: Nueva notificación."""
    type: str = "nueva_notificacion"
    notificacion: NotificacionResponse


class WSNotificacionLeida(BaseModel):
    """Mensaje WebSocket: Notificación leída."""
    type: str = "notificacion_leida"
    notificacion_id: int


class WSNotificacionesStats(BaseModel):
    """Mensaje WebSocket: Estadísticas de notificaciones."""
    type: str = "notificaciones_stats"
    stats: NotificacionStatsResponse
