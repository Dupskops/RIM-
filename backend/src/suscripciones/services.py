"""
Servicios de lógica de negocio para suscripciones.
"""
from datetime import datetime
from typing import Optional
import math

from .models import Suscripcion, PlanType, SuscripcionStatus
from .validators import calculate_end_date


class SuscripcionService:
    """Servicio con lógica de negocio para suscripciones."""
    
    @staticmethod
    def prepare_suscripcion_data(
        usuario_id: int,
        plan: str,
        duracion_meses: Optional[int] = None,
        precio: Optional[float] = None,
        metodo_pago: Optional[str] = None,
        transaction_id: Optional[str] = None,
        auto_renovacion: bool = False,
        notas: Optional[str] = None
    ) -> dict:
        """
        Prepara los datos de una suscripción para creación.
        
        Args:
            usuario_id: ID del usuario (INTEGER)
            plan: Tipo de plan
            duracion_meses: Duración en meses (solo premium)
            precio: Precio del plan
            metodo_pago: Método de pago
            transaction_id: ID de transacción
            auto_renovacion: Auto-renovación
            notas: Notas adicionales
            
        Returns:
            Diccionario con datos preparados
        """
        start_date = datetime.utcnow()
        
        # Calcular end_date según el plan
        end_date = None
        if plan == PlanType.PREMIUM and duracion_meses:
            end_date = calculate_end_date(start_date, duracion_meses)
        
        return {
            "usuario_id": usuario_id,
            "plan": plan,
            "status": SuscripcionStatus.ACTIVE,
            "start_date": start_date,
            "end_date": end_date,
            "precio": precio,
            "metodo_pago": metodo_pago.lower() if metodo_pago else None,
            "transaction_id": transaction_id,
            "auto_renovacion": auto_renovacion,
            "notas": notas
        }
    
    @staticmethod
    def can_upgrade(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """
        Verifica si una suscripción puede hacer upgrade a premium.
        
        Args:
            suscripcion: Suscripción a verificar
            
        Returns:
            Tupla (puede_upgrade, mensaje_error)
        """
        if suscripcion.plan == PlanType.PREMIUM:
            return False, "Ya tienes una suscripción premium activa"
        
        if suscripcion.status != SuscripcionStatus.ACTIVE:
            return False, "La suscripción no está activa"
        
        return True, None
    
    @staticmethod
    def can_cancel(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """
        Verifica si una suscripción puede ser cancelada.
        
        Args:
            suscripcion: Suscripción a verificar
            
        Returns:
            Tupla (puede_cancelar, mensaje_error)
        """
        if suscripcion.status == SuscripcionStatus.CANCELLED:
            return False, "La suscripción ya está cancelada"
        
        if suscripcion.status == SuscripcionStatus.EXPIRED:
            return False, "La suscripción ya expiró"
        
        return True, None
    
    @staticmethod
    def can_renew(suscripcion: Suscripcion) -> tuple[bool, Optional[str]]:
        """
        Verifica si una suscripción puede ser renovada.
        
        Args:
            suscripcion: Suscripción a verificar
            
        Returns:
            Tupla (puede_renovar, mensaje_error)
        """
        if suscripcion.plan != PlanType.PREMIUM:
            return False, "Solo suscripciones premium pueden renovarse"
        
        if suscripcion.status == SuscripcionStatus.CANCELLED:
            return False, "No se puede renovar una suscripción cancelada"
        
        return True, None
    
    @staticmethod
    def calculate_pagination(total: int, page: int, page_size: int) -> dict:
        """
        Calcula información de paginación.
        
        Args:
            total: Total de registros
            page: Página actual
            page_size: Tamaño de página
            
        Returns:
            Diccionario con información de paginación
        """
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    @staticmethod
    def build_suscripcion_response(suscripcion: Suscripcion) -> dict:
        """
        Construye el diccionario de respuesta para una suscripción.
        
        Args:
            suscripcion: Suscripción a convertir
            
        Returns:
            Diccionario con datos de la suscripción
        """
        return {
            "id": suscripcion.id,
            "usuario_id": suscripcion.usuario_id,
            "plan": suscripcion.plan,
            "status": suscripcion.status,
            "start_date": suscripcion.start_date,
            "end_date": suscripcion.end_date,
            "cancelled_at": suscripcion.cancelled_at,
            "precio": float(suscripcion.precio) if suscripcion.precio else None,
            "metodo_pago": suscripcion.metodo_pago,
            "transaction_id": suscripcion.transaction_id,
            "auto_renovacion": suscripcion.auto_renovacion,
            "notas": suscripcion.notas,
            "created_at": suscripcion.created_at,
            "updated_at": suscripcion.updated_at,
            "deleted_at": suscripcion.deleted_at,
            "is_active": suscripcion.is_active,
            "is_premium": suscripcion.is_premium,
            "is_freemium": suscripcion.is_freemium,
            "dias_restantes": suscripcion.dias_restantes
        }
