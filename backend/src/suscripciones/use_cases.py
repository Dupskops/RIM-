"""
Casos de uso para suscripciones y sistema de límites Freemium v2.3.

Implementa la lógica de aplicación que coordina servicios y repositorios
para exponer funcionalidad a las rutas API.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, cast
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Caracteristica, UsoCaracteristica
from .services import LimiteService, SuscripcionService
from .repositories import PlanesRepository, SuscripcionRepository, CaracteristicaRepository
from .schemas import (
    PlanReadSchema,
    SuscripcionReadSchema,
    LimiteCheckResponse,
    LimiteRegistroResponse,
    CaracteristicaReadSchema,
    UsoHistorialResponse,
    FeatureStatusSchema,
)

import logging

logger = logging.getLogger(__name__)


def _convert_caracteristica_to_schema(carac: Caracteristica) -> CaracteristicaReadSchema:
    """Convierte una Caracteristica ORM a CaracteristicaReadSchema.
    
    Helper function para evitar warnings de tipo en comprehensions.
    """
    return CaracteristicaReadSchema(
        id=carac.id,
        clave_funcion=carac.clave_funcion,
        descripcion=carac.descripcion,
        limite_free=carac.limite_free,
        limite_pro=carac.limite_pro,
    )


class ListPlanesUseCase:
    """Lista todos los planes disponibles."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.planes_repo = PlanesRepository(session)

    async def execute(self) -> List[PlanReadSchema]:
        """Retorna lista de planes con sus características.
        
        Returns:
            Lista de PlanReadSchema con información completa
        """
        logger.debug("ListPlanesUseCase.execute")
        
        planes = await self.planes_repo.list_planes()
        
        result: List[PlanReadSchema] = []
        for plan in planes:
            caracteristicas_list: List[CaracteristicaReadSchema] = []
            
            # SQLAlchemy relationships no tienen type hints completos
            for c in (plan.caracteristicas or []):  # type: ignore
                carac = _convert_caracteristica_to_schema(cast(Caracteristica, c))
                caracteristicas_list.append(carac)
            
            plan_schema = PlanReadSchema(
                id=plan.id,
                nombre_plan=plan.nombre_plan,
                precio=plan.precio,
                periodo_facturacion=plan.periodo_facturacion.value if plan.periodo_facturacion else None,
                caracteristicas=caracteristicas_list,
            )
            result.append(plan_schema)
        
        return result


class GetMySuscripcionUseCase:
    """Obtiene la suscripción actual del usuario."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.suscripcion_repo = SuscripcionRepository(session)
        self.caracteristica_repo = CaracteristicaRepository(session)
        self.limite_service = LimiteService(session)

    async def execute(self, usuario_id: int) -> Optional[SuscripcionReadSchema]:
        """Retorna la suscripción activa del usuario con estado de características.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            SuscripcionReadSchema o None si no tiene suscripción
        """
        logger.debug("GetMySuscripcionUseCase.execute: usuario_id=%s", usuario_id)
        
        suscripcion = await self.suscripcion_repo.get_by_usuario_id(usuario_id)
        
        if not suscripcion:
            return None
        
        # Eager loading ya debería estar hecho en el repo
        plan_data = None
        if suscripcion.plan:
            caracteristicas_list: List[CaracteristicaReadSchema] = []
            for c in (suscripcion.plan.caracteristicas or []):  # type: ignore
                carac = _convert_caracteristica_to_schema(cast(Caracteristica, c))
                caracteristicas_list.append(carac)
            
            plan_data = PlanReadSchema(
                id=suscripcion.plan.id,
                nombre_plan=suscripcion.plan.nombre_plan,
                precio=suscripcion.plan.precio,
                periodo_facturacion=suscripcion.plan.periodo_facturacion.value if suscripcion.plan.periodo_facturacion else None,
                caracteristicas=caracteristicas_list,
            )

        # --- Lógica de Estado de Características (Merged) ---
        caracteristicas_all = await self.caracteristica_repo.get_all()
        features_status: List[FeatureStatusSchema] = []
        
        es_pro = suscripcion.plan.nombre_plan.lower() != "free" if suscripcion.plan else False
        
        for carac in caracteristicas_all:
            # Obtener uso actual
            estado_limite = await self.limite_service.check_limite(usuario_id, carac.clave_funcion)
            
            uso_actual = estado_limite["usos_realizados"]
            limite_actual = estado_limite["limite"]
            limite_pro = carac.limite_pro
            
            # Generar mensaje de upsell
            upsell_msg = None
            if not es_pro:
                is_upgrade = False
                if carac.limite_free is not None:
                    if limite_pro is None:
                        is_upgrade = True
                    elif limite_pro > carac.limite_free:
                        is_upgrade = True
                
                if is_upgrade:
                    if limite_pro is None:
                        upsell_msg = "Mejora a Pro para uso ilimitado"
                    else:
                        upsell_msg = f"Mejora a Pro para obtener {limite_pro} usos"

            features_status.append(FeatureStatusSchema(
                caracteristica=carac.clave_funcion,
                descripcion=carac.descripcion,
                uso_actual=uso_actual,
                limite_actual=limite_actual,
                limite_pro=limite_pro,
                upsell_message=upsell_msg
            ))
        
        return SuscripcionReadSchema(
            id=suscripcion.id,
            usuario_id=suscripcion.usuario_id,
            plan=plan_data,
            fecha_inicio=suscripcion.fecha_inicio,
            fecha_fin=suscripcion.fecha_fin,
            estado_suscripcion=suscripcion.estado_suscripcion.value if suscripcion.estado_suscripcion else None,
            features_status=features_status,
        )


class CheckLimiteUseCase:
    """Verifica si el usuario puede usar una característica."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.limite_service = LimiteService(session)

    async def execute(
        self, 
        usuario_id: int, 
        clave_caracteristica: str
    ) -> LimiteCheckResponse:
        """Verifica límite de una característica.
        
        Args:
            usuario_id: ID del usuario
            clave_caracteristica: Clave de la característica (ej: 'CHATBOT', 'ML_PREDICTIONS')
            
        Returns:
            LimiteCheckResponse con estado del límite
        """
        logger.debug(
            "CheckLimiteUseCase.execute: usuario_id=%s caracteristica=%s",
            usuario_id, clave_caracteristica
        )
        
        result = await self.limite_service.check_limite(usuario_id, clave_caracteristica)
        
        return LimiteCheckResponse(
            puede_usar=result["puede_usar"],
            usos_realizados=result["usos_realizados"],
            limite=result["limite"],
            usos_restantes=result.get("usos_restantes"),
            mensaje=result["mensaje"],
            periodo_actual=result["periodo_actual"],
        )


class RegistrarUsoUseCase:
    """Registra el uso de una característica."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.limite_service = LimiteService(session)

    async def execute(
        self, 
        usuario_id: int, 
        clave_caracteristica: str
    ) -> LimiteRegistroResponse:
        """Registra un uso y actualiza el contador.
        
        Args:
            usuario_id: ID del usuario
            clave_caracteristica: Clave de la característica
            
        Returns:
            LimiteRegistroResponse con resultado del registro
        """
        logger.debug(
            "RegistrarUsoUseCase.execute: usuario_id=%s caracteristica=%s",
            usuario_id, clave_caracteristica
        )
        
        result = await self.limite_service.registrar_uso(usuario_id, clave_caracteristica)
        
        return LimiteRegistroResponse(
            exito=result["exito"],
            usos_realizados=result["usos_realizados"],
            limite=result["limite"],
            usos_restantes=result.get("usos_restantes"),
            mensaje=result["mensaje"],
        )


class GetHistorialUsoUseCase:
    """Obtiene el historial de uso de características del usuario."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(self, usuario_id: int) -> List[UsoHistorialResponse]:
        """Retorna historial de uso del mes actual.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de UsoHistorialResponse con uso por característica
        """
        logger.debug("GetHistorialUsoUseCase.execute: usuario_id=%s", usuario_id)
        
        from sqlalchemy import select, and_
        from datetime import date
        
        periodo_actual = date.today().replace(day=1)
        
        # Consultar uso del mes actual
        stmt = (
            select(UsoCaracteristica)
            .where(
                and_(
                    UsoCaracteristica.usuario_id == usuario_id,
                    UsoCaracteristica.periodo_mes == periodo_actual,
                    UsoCaracteristica.deleted_at.is_(None)
                )
            )
        )
        
        result = await self.session.execute(stmt)
        usos = result.scalars().all()
        
        # Obtener características con eager loading
        if not usos:
            return []
        
        # Cargar características
        caracteristica_ids = [uso.caracteristica_id for uso in usos]
        stmt_carac = select(Caracteristica).where(
            Caracteristica.id.in_(caracteristica_ids)
        )
        result_carac = await self.session.execute(stmt_carac)
        caracteristicas = {c.id: c for c in result_carac.scalars().all()}
        
        return [
            UsoHistorialResponse(
                caracteristica=caracteristicas[uso.caracteristica_id].clave_funcion,
                usos_realizados=uso.usos_realizados,
                limite_mensual=uso.limite_mensual,
                ultimo_uso_at=uso.ultimo_uso_at,
                periodo_mes=uso.periodo_mes,
            )
            for uso in usos
            if uso.caracteristica_id in caracteristicas
        ]


class CambiarPlanUseCase:
    """Cambia el plan de un usuario (genérico para cualquier plan)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.suscripcion_service = SuscripcionService(session)
        self.planes_repo = PlanesRepository(session)

    async def execute(
        self, 
        usuario_id: int, 
        nuevo_plan_id: int
    ) -> SuscripcionReadSchema:
        """Cambia el plan del usuario.
        
        Args:
            usuario_id: ID del usuario
            nuevo_plan_id: ID del plan destino
            
        Returns:
            SuscripcionReadSchema actualizada
            
        Raises:
            ValueError: Si el plan no existe o el usuario ya lo tiene
        """
        logger.info(
            "CambiarPlanUseCase.execute: usuario_id=%s nuevo_plan_id=%s",
            usuario_id, nuevo_plan_id
        )
        
        # Usar el servicio genérico
        suscripcion = await self.suscripcion_service.cambiar_plan(
            usuario_id, nuevo_plan_id
        )
        
        # Cargar plan con eager loading
        plan = await self.planes_repo.get_plan_by_id(suscripcion.plan_id)
        
        plan_data = None
        if plan:
            caracteristicas_list: List[CaracteristicaReadSchema] = []
            for c in (plan.caracteristicas or []):  # type: ignore
                carac = _convert_caracteristica_to_schema(cast(Caracteristica, c))
                caracteristicas_list.append(carac)
            
            plan_data = PlanReadSchema(
                id=plan.id,
                nombre_plan=plan.nombre_plan,
                precio=plan.precio,
                periodo_facturacion=plan.periodo_facturacion.value if plan.periodo_facturacion else None,
                caracteristicas=caracteristicas_list,
            )
        
        return SuscripcionReadSchema(
            id=suscripcion.id,
            usuario_id=suscripcion.usuario_id,
            plan=plan_data,
            fecha_inicio=suscripcion.fecha_inicio,
            fecha_fin=suscripcion.fecha_fin,
            estado_suscripcion=suscripcion.estado_suscripcion.value if suscripcion.estado_suscripcion else None,
        )


class CancelSuscripcionUseCase:
    """Cancela la suscripción activa del usuario."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.suscripcion_repo = SuscripcionRepository(session)

    async def execute(self, usuario_id: int) -> SuscripcionReadSchema:
        """Cancela la suscripción y la pasa a plan Free.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            SuscripcionReadSchema actualizada
            
        Raises:
            ValueError: Si no tiene suscripción activa
        """
        logger.info("CancelSuscripcionUseCase.execute: usuario_id=%s", usuario_id)
        
        from .models import EstadoSuscripcion
        from .repositories import PlanesRepository
        
        # Obtener suscripción actual
        suscripcion = await self.suscripcion_repo.get_by_usuario_id(usuario_id)
        
        if not suscripcion:
            raise ValueError("Usuario no tiene suscripción activa")
        
        if suscripcion.estado_suscripcion == EstadoSuscripcion.CANCELADA:
            raise ValueError("La suscripción ya está cancelada")
        
        # Buscar plan Free
        planes_repo = PlanesRepository(self.session)
        plan_free = await planes_repo.get_plan_by_nombre("FREE")
        
        if not plan_free:
            raise ValueError("Plan Free no encontrado")
        
        # Actualizar a Free y marcar como cancelada
        suscripcion.plan_id = plan_free.id
        suscripcion.estado_suscripcion = EstadoSuscripcion.CANCELADA
        suscripcion.fecha_fin = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(suscripcion)
        
        logger.info("CancelSuscripcionUseCase: Suscripción cancelada usuario_id=%s", usuario_id)
        
        # Cargar plan con eager loading
        plan = await planes_repo.get_plan_by_id(suscripcion.plan_id)
        
        plan_data = None
        if plan:
            caracteristicas_list: List[CaracteristicaReadSchema] = []
            for c in (plan.caracteristicas or []):  # type: ignore
                carac = _convert_caracteristica_to_schema(cast(Caracteristica, c))
                caracteristicas_list.append(carac)
            
            plan_data = PlanReadSchema(
                id=plan.id,
                nombre_plan=plan.nombre_plan,
                precio=plan.precio,
                periodo_facturacion=plan.periodo_facturacion.value if plan.periodo_facturacion else None,
                caracteristicas=caracteristicas_list,
            )
        
        return SuscripcionReadSchema(
            id=suscripcion.id,
            usuario_id=suscripcion.usuario_id,
            plan=plan_data,
            fecha_inicio=suscripcion.fecha_inicio,
            fecha_fin=suscripcion.fecha_fin,
            estado_suscripcion=suscripcion.estado_suscripcion.value if suscripcion.estado_suscripcion else None,
        )


__all__ = [
    "ListPlanesUseCase",
    "GetMySuscripcionUseCase",
    "CheckLimiteUseCase",
    "RegistrarUsoUseCase",
    "GetHistorialUsoUseCase",
    "CambiarPlanUseCase",
    "CancelSuscripcionUseCase",
]
