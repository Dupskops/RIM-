"""
Servicios de lógica de negocio para suscripciones y límites Freemium v2.3.

Este módulo implementa la lógica核心 del sistema de límites mensuales:
- Verificación de límites por característica
- Registro de uso con actualización de contadores
- Reset automático mensual
- Cálculo de uso restante
"""
from __future__ import annotations

from datetime import datetime, date, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from .models import (
    Plan,
    Caracteristica,
    Suscripcion,
    UsoCaracteristica,
    EstadoSuscripcion,
)

import logging

logger = logging.getLogger(__name__)


class LimiteService:
    """Servicio para gestión de límites de características (v2.3 Freemium).
    
    Implementa las funciones SQL:
    - check_caracteristica_limite()
    - registrar_uso_caracteristica()
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_limite(
        self,
        usuario_id: int,
        clave_caracteristica: str
    ) -> Dict[str, Any]:
        """Verifica si el usuario puede usar una característica.
        
        Equivalente a la función SQL check_caracteristica_limite().
        
        Args:
            usuario_id: ID del usuario
            clave_caracteristica: Clave de la característica (ej: 'CHATBOT', 'ML_PREDICTIONS')
            
        Returns:
            Dict con:
            - puede_usar: bool
            - usos_realizados: int
            - limite: int | None
            - usos_restantes: int | None
            - mensaje: str
            - periodo_actual: date
        """
        logger.debug(
            "LimiteService.check_limite: usuario_id=%s caracteristica=%s",
            usuario_id, clave_caracteristica
        )

        # Obtener periodo actual (primer día del mes)
        periodo_actual = date.today().replace(day=1)

        # Obtener característica
        stmt_carac = select(Caracteristica).where(
            Caracteristica.clave_funcion == clave_caracteristica
        )
        result_carac = await self.session.execute(stmt_carac)
        caracteristica = result_carac.scalar_one_or_none()

        if not caracteristica:
            logger.warning("check_limite: Característica no encontrada: %s", clave_caracteristica)
            return {
                "puede_usar": False,
                "usos_realizados": 0,
                "limite": None,
                "usos_restantes": None,
                "mensaje": f"Característica '{clave_caracteristica}' no existe",
                "periodo_actual": periodo_actual,
            }

        # Obtener suscripción del usuario
        stmt_sus = select(Suscripcion).where(
            Suscripcion.usuario_id == usuario_id
        )
        result_sus = await self.session.execute(stmt_sus)
        suscripcion = result_sus.scalar_one_or_none()

        if not suscripcion:
            logger.warning("check_limite: Usuario sin suscripción: %s", usuario_id)
            return {
                "puede_usar": False,
                "usos_realizados": 0,
                "limite": None,
                "usos_restantes": None,
                "mensaje": "Usuario sin suscripción activa",
                "periodo_actual": periodo_actual,
            }

        # Obtener plan con eager loading
        stmt_plan = select(Plan).where(Plan.id == suscripcion.plan_id)
        result_plan = await self.session.execute(stmt_plan)
        plan = result_plan.scalar_one_or_none()

        if not plan:
            logger.warning("check_limite: Plan no encontrado: %s", suscripcion.plan_id)
            return {
                "puede_usar": False,
                "usos_realizados": 0,
                "limite": None,
                "usos_restantes": None,
                "mensaje": "Plan no encontrado",
                "periodo_actual": periodo_actual,
            }

        # Determinar límite según el plan
        plan_nombre = plan.nombre_plan.lower()
        if "free" in plan_nombre:
            limite = caracteristica.limite_free
        elif "pro" in plan_nombre:
            limite = caracteristica.limite_pro
        else:
            limite = caracteristica.limite_free  # Default a Free

        # Si límite es NULL = ilimitado
        if limite is None:
            logger.debug("check_limite: Característica ilimitada para plan %s", plan_nombre)
            return {
                "puede_usar": True,
                "usos_realizados": 0,
                "limite": None,
                "usos_restantes": None,
                "mensaje": "Uso ilimitado",
                "periodo_actual": periodo_actual,
            }

        # Si límite es 0 = bloqueado
        if limite == 0:
            logger.debug("check_limite: Característica bloqueada para plan %s", plan_nombre)
            return {
                "puede_usar": False,
                "usos_realizados": 0,
                "limite": 0,
                "usos_restantes": 0,
                "mensaje": f"Característica no disponible en plan {plan.nombre_plan}. Upgrade a Pro.",
                "periodo_actual": periodo_actual,
            }

        # Buscar uso actual del mes
        stmt_uso = select(UsoCaracteristica).where(
            and_(
                UsoCaracteristica.usuario_id == usuario_id,
                UsoCaracteristica.caracteristica_id == caracteristica.id,
                UsoCaracteristica.periodo_mes == periodo_actual,
                UsoCaracteristica.deleted_at.is_(None)
            )
        )
        result_uso = await self.session.execute(stmt_uso)
        uso = result_uso.scalar_one_or_none()

        if not uso:
            # No hay registro de uso este mes, puede usar
            logger.debug("check_limite: Sin uso previo este mes, puede usar")
            return {
                "puede_usar": True,
                "usos_realizados": 0,
                "limite": limite,
                "usos_restantes": limite,
                "mensaje": f"Disponible: {limite} usos este mes",
                "periodo_actual": periodo_actual,
            }

        # Hay registro, verificar si alcanzó el límite
        usos_realizados = uso.usos_realizados
        usos_restantes = limite - usos_realizados

        if usos_realizados >= limite:
            logger.info(
                "check_limite: Límite alcanzado usuario=%s caracteristica=%s (%d/%d)",
                usuario_id, clave_caracteristica, usos_realizados, limite
            )
            return {
                "puede_usar": False,
                "usos_realizados": usos_realizados,
                "limite": limite,
                "usos_restantes": 0,
                "mensaje": f"Límite alcanzado: {usos_realizados}/{limite} usos este mes",
                "periodo_actual": periodo_actual,
            }

        logger.debug(
            "check_limite: Puede usar, restantes=%d/%d",
            usos_restantes, limite
        )
        return {
            "puede_usar": True,
            "usos_realizados": usos_realizados,
            "limite": limite,
            "usos_restantes": usos_restantes,
            "mensaje": f"Disponible: {usos_restantes}/{limite} usos restantes",
            "periodo_actual": periodo_actual,
        }

    async def registrar_uso(
        self,
        usuario_id: int,
        clave_caracteristica: str
    ) -> Dict[str, Any]:
        """Registra un uso de la característica y actualiza el contador.
        
        Equivalente a la función SQL registrar_uso_caracteristica().
        
        Args:
            usuario_id: ID del usuario
            clave_caracteristica: Clave de la característica
            
        Returns:
            Dict con:
            - exito: bool
            - usos_realizados: int
            - limite: int
            - usos_restantes: int
            - mensaje: str
        """
        logger.debug(
            "LimiteService.registrar_uso: usuario_id=%s caracteristica=%s",
            usuario_id, clave_caracteristica
        )

        # Primero verificar si puede usar
        check_result = await self.check_limite(usuario_id, clave_caracteristica)

        if not check_result["puede_usar"]:
            logger.warning(
                "registrar_uso: No puede usar característica: %s",
                check_result["mensaje"]
            )
            return {
                "exito": False,
                "usos_realizados": check_result["usos_realizados"],
                "limite": check_result["limite"],
                "usos_restantes": check_result.get("usos_restantes", 0),
                "mensaje": check_result["mensaje"],
            }

        # Obtener IDs necesarios
        periodo_actual = check_result["periodo_actual"]

        stmt_carac = select(Caracteristica).where(
            Caracteristica.clave_funcion == clave_caracteristica
        )
        result_carac = await self.session.execute(stmt_carac)
        caracteristica = result_carac.scalar_one()

        stmt_sus = select(Suscripcion).where(
            Suscripcion.usuario_id == usuario_id
        )
        result_sus = await self.session.execute(stmt_sus)
        suscripcion = result_sus.scalar_one()

        stmt_plan = select(Plan).where(Plan.id == suscripcion.plan_id)
        result_plan = await self.session.execute(stmt_plan)
        plan = result_plan.scalar_one()

        # Determinar límite
        plan_nombre = plan.nombre_plan.lower()
        limite = caracteristica.limite_free if "free" in plan_nombre else caracteristica.limite_pro

        # Si es ilimitado, no registrar (no tiene sentido)
        if limite is None:
            logger.debug("registrar_uso: Característica ilimitada, no se registra")
            return {
                "exito": True,
                "usos_realizados": 0,
                "limite": None,
                "usos_restantes": None,
                "mensaje": "Uso registrado (ilimitado)",
            }

        # Buscar o crear registro de uso
        stmt_uso = select(UsoCaracteristica).where(
            and_(
                UsoCaracteristica.usuario_id == usuario_id,
                UsoCaracteristica.caracteristica_id == caracteristica.id,
                UsoCaracteristica.periodo_mes == periodo_actual,
                UsoCaracteristica.deleted_at.is_(None)
            )
        )
        result_uso = await self.session.execute(stmt_uso)
        uso = result_uso.scalar_one_or_none()

        if not uso:
            # Crear nuevo registro
            uso = UsoCaracteristica(
                usuario_id=usuario_id,
                caracteristica_id=caracteristica.id,
                periodo_mes=periodo_actual,
                usos_realizados=1,
                limite_mensual=limite,
                ultimo_uso_at=datetime.now(timezone.utc),
            )
            self.session.add(uso)
            logger.info(
                "registrar_uso: Nuevo registro creado usuario=%s caracteristica=%s (1/%d)",
                usuario_id, clave_caracteristica, limite
            )
        else:
            # Actualizar existente
            uso.usos_realizados += 1
            uso.ultimo_uso_at = datetime.now(timezone.utc)
            logger.info(
                "registrar_uso: Uso actualizado usuario=%s caracteristica=%s (%d/%d)",
                usuario_id, clave_caracteristica, uso.usos_realizados, limite
            )

        await self.session.commit()
        await self.session.refresh(uso)

        usos_restantes = limite - uso.usos_realizados

        return {
            "exito": True,
            "usos_realizados": uso.usos_realizados,
            "limite": limite,
            "usos_restantes": usos_restantes,
            "mensaje": f"Uso registrado. Restantes: {usos_restantes}/{limite}",
        }


class SuscripcionService:
    """Servicio para gestión de suscripciones y planes."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_suscripcion_usuario(self, usuario_id: int) -> Optional[Suscripcion]:
        """Obtiene la suscripción activa del usuario."""
        stmt = select(Suscripcion).where(
            Suscripcion.usuario_id == usuario_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def cambiar_plan(
        self, 
        usuario_id: int, 
        nuevo_plan_id: int
    ) -> Suscripcion:
        """Cambia el plan de un usuario (genérico para cualquier upgrade/downgrade).
        
        Args:
            usuario_id: ID del usuario
            nuevo_plan_id: ID del plan destino
            
        Returns:
            Suscripcion actualizada
            
        Raises:
            ValueError: Si no se encuentra el plan o el usuario ya tiene ese plan
        """
        logger.info(
            "SuscripcionService.cambiar_plan: usuario_id=%s nuevo_plan_id=%s",
            usuario_id, nuevo_plan_id
        )

        # Verificar que el plan destino existe (usando repository)
        from .repositories import PlanesRepository
        planes_repo = PlanesRepository(self.session)
        nuevo_plan = await planes_repo.get_plan_by_id(nuevo_plan_id)

        if not nuevo_plan:
            raise ValueError(f"Plan con ID {nuevo_plan_id} no encontrado")

        # Obtener suscripción actual
        suscripcion = await self.get_suscripcion_usuario(usuario_id)

        if not suscripcion:
            # Crear nueva suscripción con el plan solicitado
            suscripcion = Suscripcion(
                usuario_id=usuario_id,
                plan_id=nuevo_plan_id,
                fecha_inicio=datetime.now(timezone.utc),
                fecha_fin=None,
                estado_suscripcion=EstadoSuscripcion.ACTIVA,
            )
            self.session.add(suscripcion)
            logger.info(
                "cambiar_plan: Nueva suscripción creada para usuario %s con plan %s",
                usuario_id, nuevo_plan.nombre_plan
            )
        else:
            # Verificar si ya tiene el mismo plan
            if suscripcion.plan_id == nuevo_plan_id:
                raise ValueError(
                    f"Usuario ya tiene el plan '{nuevo_plan.nombre_plan}' activo"
                )

            # Actualizar al nuevo plan
            plan_anterior_id = suscripcion.plan_id
            suscripcion.plan_id = nuevo_plan_id
            suscripcion.fecha_inicio = datetime.now(timezone.utc)
            suscripcion.fecha_fin = None
            suscripcion.estado_suscripcion = EstadoSuscripcion.ACTIVA

            logger.info(
                "cambiar_plan: Usuario %s cambió de plan_id=%s a plan_id=%s (%s)",
                usuario_id, plan_anterior_id, nuevo_plan_id, nuevo_plan.nombre_plan
            )
            
            # Guardar cambios primero
            await self.session.commit()
            await self.session.refresh(suscripcion)
            
            # Emitir evento de cambio de plan para enviar email
            try:
                from .events import emit_plan_changed
                
                # Obtener nombre del plan anterior
                plan_anterior = await planes_repo.get_plan_by_id(plan_anterior_id)
                plan_anterior_nombre = plan_anterior.nombre_plan if plan_anterior else "Unknown"
                
                await emit_plan_changed(
                    suscripcion_id=suscripcion.id,
                    usuario_id=usuario_id,
                    plan_anterior_id=plan_anterior_id,
                    plan_anterior_nombre=plan_anterior_nombre,
                    plan_nuevo_id=nuevo_plan_id,
                    plan_nuevo_nombre=nuevo_plan.nombre_plan,
                    changed_by=usuario_id
                )
                logger.info(f"Evento PlanChangedEvent emitido para usuario {usuario_id}")
            except Exception as e:
                logger.warning(f"Error al emitir evento de cambio de plan: {e}")
                # No fallar el cambio de plan si falla el envío del email
            
            return suscripcion

        await self.session.commit()
        await self.session.refresh(suscripcion)
        return suscripcion


__all__ = [
    "LimiteService",
    "SuscripcionService",
]
