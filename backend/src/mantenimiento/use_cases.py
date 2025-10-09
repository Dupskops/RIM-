"""
Casos de uso para el módulo de mantenimiento.
"""
from datetime import datetime, date
from typing import Optional, List, Tuple

from src.mantenimiento.models import Mantenimiento
from src.mantenimiento.repositories import MantenimientoRepository
from src.mantenimiento.schemas import (
    MantenimientoCreate,
    MantenimientoMLCreate,
    MantenimientoUpdate,
    MantenimientoIniciar,
    MantenimientoCompletar,
    MantenimientoStatsResponse,
    MantenimientoFilterParams
)
from src.shared.base_models import PaginationParams
from src.mantenimiento import services, validators
from src.mantenimiento.events import (
    MantenimientoProgramadoEvent,
    MantenimientoUrgenteEvent,
    MantenimientoVencidoEvent,
    MantenimientoIniciadoEvent,
    MantenimientoCompletadoEvent,
    MantenimientoRecomendadoIAEvent,
    AlertaMantenimientoProximoEvent
)
from src.shared.event_bus import event_bus
from src.shared.exceptions import ResourceNotFoundException, ValidationException
from src.shared.constants import EstadoMantenimiento


class CreateMantenimientoUseCase:
    """Caso de uso para crear un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, data: MantenimientoCreate) -> Mantenimiento:
        """Crea un nuevo mantenimiento."""
        # Generar código único
        codigo = services.generate_codigo_mantenimiento()
        
        # Calcular valores automáticos
        if data.costo_estimado is None:
            costo_estimado = services.calculate_costo_estimado(data.tipo)
        else:
            costo_estimado = data.costo_estimado
        
        prioridad = data.prioridad or services.calculate_prioridad_base(
            data.tipo, 
            data.es_preventivo
        )
        
        # Calcular fecha de vencimiento si no se proporciona
        if data.fecha_vencimiento is None and data.fecha_programada:
            fecha_vencimiento = services.calculate_fecha_vencimiento(
                data.tipo,
                data.fecha_programada
            )
        else:
            fecha_vencimiento = data.fecha_vencimiento
        
        # Generar descripción si no se proporciona
        descripcion = data.descripcion or services.generate_descripcion_automatica(
            data.tipo,
            data.kilometraje_actual,
            data.es_preventivo
        )
        
        # Determinar urgencia
        dias_vencimiento = None
        if fecha_vencimiento:
            dias_vencimiento = (fecha_vencimiento - date.today()).days
        
        es_urgente = services.determine_urgencia(
            dias_vencimiento,
            prioridad,
            data.falla_relacionada_id is not None
        )
        
        # Calcular kilometraje siguiente si no se proporciona
        if data.kilometraje_siguiente is None:
            kilometraje_siguiente = validators.calculate_kilometraje_siguiente(
                data.tipo,
                data.kilometraje_actual
            )
        else:
            kilometraje_siguiente = data.kilometraje_siguiente
        
        # Crear mantenimiento
        mantenimiento = Mantenimiento(
            codigo=codigo,
            moto_id=data.moto_id,
            tipo=data.tipo,
            estado=EstadoMantenimiento.PENDIENTE,
            es_preventivo=data.es_preventivo,
            falla_relacionada_id=data.falla_relacionada_id,
            kilometraje_actual=data.kilometraje_actual,
            kilometraje_siguiente=kilometraje_siguiente,
            fecha_programada=data.fecha_programada,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion,
            mecanico_asignado=data.mecanico_asignado,
            taller_realizado=data.taller_realizado,
            costo_estimado=costo_estimado,
            prioridad=prioridad,
            es_urgente=es_urgente,
            dias_anticipacion_alerta=data.dias_anticipacion_alerta,
            recomendado_por_ia=False
        )
        
        mantenimiento = await self.repository.create(mantenimiento)
        
        # Emitir evento
        event = MantenimientoProgramadoEvent(
            mantenimiento_id=mantenimiento.id,
            moto_id=mantenimiento.moto_id,
            tipo=mantenimiento.tipo.value,
            fecha_programada=str(mantenimiento.fecha_programada) if mantenimiento.fecha_programada else None,
            es_preventivo=mantenimiento.es_preventivo,
            prioridad=mantenimiento.prioridad,
            descripcion=mantenimiento.descripcion
        )
        await event_bus.publish(event)
        
        # Emitir evento de urgencia si aplica
        if mantenimiento.es_urgente:
            urgente_event = MantenimientoUrgenteEvent(
                mantenimiento_id=mantenimiento.id,
                moto_id=mantenimiento.moto_id,
                tipo=mantenimiento.tipo.value,
                motivo_urgencia="Mantenimiento marcado como urgente",
                prioridad=mantenimiento.prioridad,
                requiere_atencion_inmediata=True
            )
            await event_bus.publish(urgente_event)
        
        return mantenimiento


class CreateMantenimientoMLUseCase:
    """Caso de uso para crear mantenimiento recomendado por IA."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, data: MantenimientoMLCreate) -> Mantenimiento:
        """Crea un mantenimiento recomendado por IA."""
        codigo = services.generate_codigo_mantenimiento()
        
        # Calcular valores
        costo_estimado = services.calculate_costo_estimado(data.tipo)
        
        if data.fecha_vencimiento is None:
            fecha_vencimiento = services.calculate_fecha_vencimiento(data.tipo)
        else:
            fecha_vencimiento = data.fecha_vencimiento
        
        descripcion = f"[IA] {services.generate_descripcion_automatica(data.tipo, data.kilometraje_actual, True)}"
        
        kilometraje_siguiente = validators.calculate_kilometraje_siguiente(
            data.tipo,
            data.kilometraje_actual
        )
        
        # Crear mantenimiento
        mantenimiento = Mantenimiento(
            codigo=codigo,
            moto_id=data.moto_id,
            tipo=data.tipo,
            estado=EstadoMantenimiento.PENDIENTE,
            es_preventivo=True,
            kilometraje_actual=data.kilometraje_actual,
            kilometraje_siguiente=kilometraje_siguiente,
            fecha_vencimiento=fecha_vencimiento,
            descripcion=descripcion,
            costo_estimado=costo_estimado,
            prioridad=data.prioridad,
            es_urgente=data.es_urgente,
            recomendado_por_ia=True,
            confianza_prediccion=data.confianza_prediccion,
            modelo_ia_usado=data.modelo_ia_usado
        )
        
        mantenimiento = await self.repository.create(mantenimiento)
        
        # Emitir evento de recomendación IA
        event = MantenimientoRecomendadoIAEvent(
            mantenimiento_id=mantenimiento.id,
            moto_id=mantenimiento.moto_id,
            tipo=mantenimiento.tipo.value,
            confianza=mantenimiento.confianza_prediccion or 0.0,
            modelo_usado=mantenimiento.modelo_ia_usado or "",
            razon_recomendacion=f"IA detectó necesidad de {mantenimiento.tipo.value}",
            prioridad_sugerida=mantenimiento.prioridad,
            fecha_sugerida=str(mantenimiento.fecha_vencimiento) if mantenimiento.fecha_vencimiento else None
        )
        await event_bus.publish(event)
        
        return mantenimiento


class UpdateMantenimientoUseCase:
    """Caso de uso para actualizar un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, mantenimiento_id: int, data: MantenimientoUpdate) -> Mantenimiento:
        """Actualiza un mantenimiento existente."""
        mantenimiento = await self.repository.get_by_id(mantenimiento_id)
        if not mantenimiento:
            raise ResourceNotFoundException("Mantenimiento", str(mantenimiento_id))
        
        # Validar que se pueda actualizar
        if not validators.can_update_mantenimiento(mantenimiento):
            raise ValidationException("No se puede actualizar un mantenimiento completado")
        
        # Validar transición de estado si se proporciona
        if data.estado and data.estado != mantenimiento.estado:
            if not validators.validate_transition_estado(mantenimiento.estado, data.estado):
                raise ValidationException(
                    f"Transición de estado inválida: {mantenimiento.estado.value} -> {data.estado.value}"
                )
        
        # Actualizar campos
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mantenimiento, field, value)
        
        mantenimiento = await self.repository.update(mantenimiento)
        
        return mantenimiento


class IniciarMantenimientoUseCase:
    """Caso de uso para iniciar un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, mantenimiento_id: int, data: MantenimientoIniciar) -> Mantenimiento:
        """Inicia un mantenimiento."""
        mantenimiento = await self.repository.get_by_id(mantenimiento_id)
        if not mantenimiento:
            raise ResourceNotFoundException("Mantenimiento", str(mantenimiento_id))
        
        # Validar que se pueda iniciar
        if not validators.can_iniciar_mantenimiento(mantenimiento):
            raise ValidationException(
                f"No se puede iniciar mantenimiento en estado {mantenimiento.estado.value}"
            )
        
        # Actualizar estado y datos
        mantenimiento.estado = EstadoMantenimiento.EN_PROCESO
        mantenimiento.fecha_inicio = datetime.utcnow()
        
        if data.mecanico_asignado:
            mantenimiento.mecanico_asignado = data.mecanico_asignado
        if data.taller_realizado:
            mantenimiento.taller_realizado = data.taller_realizado
        if data.notas_tecnico:
            mantenimiento.notas_tecnico = data.notas_tecnico
        
        mantenimiento = await self.repository.update(mantenimiento)
        
        # Emitir evento
        event = MantenimientoIniciadoEvent(
            mantenimiento_id=mantenimiento.id,
            moto_id=mantenimiento.moto_id,
            tipo=mantenimiento.tipo.value,
            mecanico_asignado=mantenimiento.mecanico_asignado or "",
            taller=mantenimiento.taller_realizado or "",
            fecha_inicio=str(mantenimiento.fecha_inicio)
        )
        await event_bus.publish(event)
        
        return mantenimiento


class CompletarMantenimientoUseCase:
    """Caso de uso para completar un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, mantenimiento_id: int, data: MantenimientoCompletar) -> Mantenimiento:
        """Completa un mantenimiento."""
        mantenimiento = await self.repository.get_by_id(mantenimiento_id)
        if not mantenimiento:
            raise ResourceNotFoundException("Mantenimiento", str(mantenimiento_id))
        
        # Validar que se pueda completar
        if not validators.can_completar_mantenimiento(mantenimiento):
            raise ValidationException(
                f"No se puede completar mantenimiento en estado {mantenimiento.estado.value}"
            )
        
        # Validar datos de completado
        if not validators.validate_mantenimiento_completado(data.notas_tecnico, data.costo_real):
            raise ValidationException("Datos de completado inválidos")
        
        # Actualizar estado y datos
        mantenimiento.estado = EstadoMantenimiento.COMPLETADO
        mantenimiento.fecha_completado = datetime.utcnow()
        mantenimiento.notas_tecnico = data.notas_tecnico
        mantenimiento.repuestos_usados = data.repuestos_usados or ""
        mantenimiento.costo_real = data.costo_real
        mantenimiento.costo_repuestos = data.costo_repuestos
        mantenimiento.costo_mano_obra = data.costo_mano_obra
        
        if data.kilometraje_siguiente:
            mantenimiento.kilometraje_siguiente = data.kilometraje_siguiente
        
        mantenimiento = await self.repository.update(mantenimiento)
        
        # Emitir evento
        duracion = mantenimiento.duracion_servicio or 0
        event = MantenimientoCompletadoEvent(
            mantenimiento_id=mantenimiento.id,
            moto_id=mantenimiento.moto_id,
            tipo=mantenimiento.tipo.value,
            duracion_horas=duracion,
            costo_total=mantenimiento.costo_total or 0.0,
            kilometraje_siguiente=mantenimiento.kilometraje_siguiente,
            fecha_completado=str(mantenimiento.fecha_completado),
            repuestos_usados=mantenimiento.repuestos_usados or ""
        )
        await event_bus.publish(event)
        
        return mantenimiento


class GetMantenimientoUseCase:
    """Caso de uso para obtener un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, mantenimiento_id: int) -> Mantenimiento:
        """Obtiene un mantenimiento por ID."""
        mantenimiento = await self.repository.get_by_id(mantenimiento_id)
        if not mantenimiento:
            raise ResourceNotFoundException("Mantenimiento", str(mantenimiento_id))
        return mantenimiento


class ListMantenimientosByMotoUseCase:
    """Caso de uso para listar mantenimientos de una moto."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(
        self,
        filters: MantenimientoFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Mantenimiento], int]:
        """Lista mantenimientos con filtros y paginación."""
        # Construir query base con filtros
        # Por ahora, solo aplicamos moto_id y solo_activos
        mantenimientos = await self.repository.get_by_moto(
            filters.moto_id,
            skip=pagination.offset,
            limit=pagination.limit,
            solo_activos=filters.solo_activos or False
        )
        
        # Obtener total (TODO: implementar conteo real con filtros en repository)
        total = await self.repository.count_by_moto(filters.moto_id) if filters.moto_id else len(mantenimientos)
        
        return mantenimientos, total


class GetMantenimientoStatsUseCase:
    """Caso de uso para obtener estadísticas de mantenimientos."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, moto_id: Optional[int] = None) -> MantenimientoStatsResponse:
        """Obtiene estadísticas de mantenimientos."""
        # Obtener mantenimientos
        if moto_id:
            mantenimientos = await self.repository.get_by_moto(moto_id, limit=1000)
        else:
            mantenimientos = await self.repository.get_historial_moto(0, limit=1000)  # type: ignore
        
        # Calcular estadísticas
        total = len(mantenimientos)
        pendientes = sum(1 for m in mantenimientos if m.estado == EstadoMantenimiento.PENDIENTE)
        programados = sum(1 for m in mantenimientos if m.estado == EstadoMantenimiento.PROGRAMADO)
        en_proceso = sum(1 for m in mantenimientos if m.estado == EstadoMantenimiento.EN_PROCESO)
        completados = sum(1 for m in mantenimientos if m.estado == EstadoMantenimiento.COMPLETADO)
        cancelados = sum(1 for m in mantenimientos if m.estado == EstadoMantenimiento.CANCELADO)
        vencidos = sum(1 for m in mantenimientos if m.esta_vencido)
        urgentes = sum(1 for m in mantenimientos if m.es_urgente)
        
        # Por tipo
        por_tipo = await self.repository.get_stats_by_tipo()
        
        # Costos
        costo_total_estimado = sum(m.costo_estimado or 0 for m in mantenimientos)
        costo_total_real = await self.repository.get_costo_total(moto_id)
        costo_promedio = services.calculate_costo_promedio(mantenimientos)
        
        # Tiempos
        duracion_promedio = await self.repository.get_duracion_promedio()
        
        # IA
        recomendados_ia = sum(1 for m in mantenimientos if m.recomendado_por_ia)
        confianzas = [m.confianza_prediccion for m in mantenimientos if m.confianza_prediccion is not None]
        confianza_promedio_ia = sum(confianzas) / len(confianzas) if confianzas else None
        
        return MantenimientoStatsResponse(
            total_mantenimientos=total,
            pendientes=pendientes,
            programados=programados,
            en_proceso=en_proceso,
            completados=completados,
            cancelados=cancelados,
            vencidos=vencidos,
            urgentes=urgentes,
            por_tipo=por_tipo,
            costo_total_estimado=costo_total_estimado,
            costo_total_real=costo_total_real,
            costo_promedio=costo_promedio,
            duracion_promedio_horas=duracion_promedio,
            recomendados_por_ia=recomendados_ia,
            confianza_promedio_ia=confianza_promedio_ia
        )


class DeleteMantenimientoUseCase:
    """Caso de uso para eliminar un mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, mantenimiento_id: int) -> None:
        """Elimina un mantenimiento (soft delete)."""
        mantenimiento = await self.repository.get_by_id(mantenimiento_id)
        if not mantenimiento:
            raise ResourceNotFoundException("Mantenimiento", str(mantenimiento_id))
        
        # Validar que se pueda eliminar
        if not validators.can_delete_mantenimiento(mantenimiento):
            raise ValidationException(
                f"No se puede eliminar mantenimiento en estado {mantenimiento.estado.value}"
            )
        
        await self.repository.delete(mantenimiento)


class CheckAlertasMantenimientoUseCase:
    """Caso de uso para verificar y enviar alertas de mantenimiento."""
    
    def __init__(self, repository: MantenimientoRepository):
        self.repository = repository
    
    async def execute(self, dias: int = 7) -> List[Mantenimiento]:
        """Verifica mantenimientos próximos a vencer y emite alertas."""
        mantenimientos = await self.repository.get_proximos_a_vencer(dias=dias, limit=100)
        
        for mantenimiento in mantenimientos:
            if services.should_send_alert(mantenimiento):
                # Emitir evento de alerta
                event = AlertaMantenimientoProximoEvent(
                    mantenimiento_id=mantenimiento.id,
                    moto_id=mantenimiento.moto_id,
                    tipo=mantenimiento.tipo.value,
                    dias_restantes=mantenimiento.dias_hasta_vencimiento or 0,
                    fecha_programada=str(mantenimiento.fecha_programada) if mantenimiento.fecha_programada else "",
                    descripcion=mantenimiento.descripcion,
                    es_urgente=mantenimiento.es_urgente
                )
                await event_bus.publish(event)
                
                # Marcar alerta como enviada
                await self.repository.marcar_alerta_enviada(mantenimiento.id)
        
        return mantenimientos
