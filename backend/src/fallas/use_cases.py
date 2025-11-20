"""
Casos de uso del módulo de fallas.
Orquesta la lógica de negocio y coordina entre repositorios y servicios.
"""
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Falla
from .schemas import (
    FallaCreate,
    FallaMLCreate,
    FallaUpdate,
    FallaDiagnosticar,
    FallaResolver,
    FallaStatsResponse,
    FallaFilterParams
)
from .repositories import FallaRepository
from .services import (
    generate_codigo_falla,
    determine_severidad_from_sensor,
    determine_puede_conducir,
    generate_solucion_sugerida,
    estimate_costo_reparacion,
    should_emit_critical_event,
    calcular_tasa_resolucion,
    calcular_tiempo_promedio_resolucion
)
from .validators import (
    validate_tipo_falla,
    validate_severidad,
    validate_transition_estado,
    can_update_falla,
    validate_fechas,
    calculate_dias_resolucion
)
from .events import (
    FallaDetectadaEvent,
    FallaCriticaEvent,
    FallaDiagnosticadaEvent,
    FallaResueltaEvent
)
from ..shared.exceptions import ResourceNotFoundException, ResourceAlreadyExistsException
from ..shared.constants import EstadoFalla
from ..shared.base_models import PaginationParams


class CreateFallaUseCase:
    """Caso de uso para crear una nueva falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        data: FallaCreate,
        usuario_id: Optional[int] = None
    ) -> Falla:
        """
        Crea una nueva falla.
        
        Args:
            data: Datos de la falla
            usuario_id: ID del usuario que reporta (opcional)
            
        Returns:
            Falla creada
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validar tipo y severidad
        validate_tipo_falla(data.tipo)
        validate_severidad(data.severidad)
        
        # Generar código único
        codigo = generate_codigo_falla()
        
        # Verificar que no exista el código (por si acaso)
        existing = await self.repo.get_by_codigo(codigo)
        if existing:
            # Regenerar si existe (muy improbable)
            codigo = generate_codigo_falla()
        
        # Determinar si puede conducir si no se especificó
        puede_conducir = data.puede_conducir
        if puede_conducir is None:
            puede_conducir = determine_puede_conducir(data.tipo, data.severidad)
        
        # Generar solución sugerida si no se proporcionó
        solucion_sugerida = data.solucion_sugerida
        if not solucion_sugerida:
            solucion_sugerida = generate_solucion_sugerida(data.tipo, data.severidad)
        
        # Crear modelo
        falla = Falla(
            moto_id=data.moto_id,
            sensor_id=data.sensor_id,
            usuario_id=usuario_id,
            codigo=codigo,
            tipo=data.tipo,
            titulo=data.titulo,
            descripcion=data.descripcion,
            severidad=data.severidad,
            estado=EstadoFalla.DETECTADA.value,
            origen_deteccion=data.origen_deteccion,
            valor_actual=data.valor_actual,
            valor_esperado=data.valor_esperado,
            requiere_atencion_inmediata=data.requiere_atencion_inmediata,
            puede_conducir=puede_conducir,
            solucion_sugerida=solucion_sugerida,
            fecha_deteccion=datetime.now(timezone.utc)
        )
        
        # Guardar en BD
        falla = await self.repo.create(falla)
        
        # Emitir evento de falla detectada
        await FallaDetectadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            severidad=falla.severidad,
            titulo=falla.titulo,
            descripcion=falla.descripcion,
            requiere_atencion_inmediata=falla.requiere_atencion_inmediata,
            puede_conducir=falla.puede_conducir,
            origen_deteccion=falla.origen_deteccion,
            usuario_id=usuario_id,
            sensor_id=falla.sensor_id
        ).emit()
        
        # Si es crítica, emitir evento crítico también
        if should_emit_critical_event(falla):
            await FallaCriticaEvent(
                falla_id=falla.id,
                moto_id=falla.moto_id,
                tipo=falla.tipo,
                titulo=falla.titulo,
                descripcion=falla.descripcion,
                puede_conducir=falla.puede_conducir,
                usuario_id=usuario_id
            ).emit()
        
        return falla


class CreateFallaMLUseCase:
    """Caso de uso para crear falla detectada por ML."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, data: FallaMLCreate) -> Falla:
        """
        Crea una falla detectada por ML/IA.
        
        Args:
            data: Datos de la falla ML
            
        Returns:
            Falla creada
        """
        # Validar
        validate_tipo_falla(data.tipo)
        validate_severidad(data.severidad)
        
        # Generar código
        codigo = generate_codigo_falla()
        
        # Determinar si puede conducir
        puede_conducir = data.puede_conducir
        if puede_conducir is None:
            puede_conducir = determine_puede_conducir(data.tipo, data.severidad)
        
        # Crear falla
        falla = Falla(
            moto_id=data.moto_id,
            sensor_id=data.sensor_id,
            codigo=codigo,
            tipo=data.tipo,
            titulo=data.titulo,
            descripcion=data.descripcion,
            severidad=data.severidad,
            estado=EstadoFalla.DETECTADA.value,
            origen_deteccion="ml",
            valor_actual=data.valor_actual,
            valor_esperado=data.valor_esperado,
            confianza_ml=data.confianza_ml,
            modelo_ml_usado=data.modelo_ml_usado,
            prediccion_ml=data.prediccion_ml,
            requiere_atencion_inmediata=data.requiere_atencion_inmediata,
            puede_conducir=puede_conducir,
            solucion_sugerida=data.solucion_sugerida or generate_solucion_sugerida(data.tipo, data.severidad),
            fecha_deteccion=datetime.now(timezone.utc)
        )
        
        falla = await self.repo.create(falla)
        
        # Emitir eventos
        await FallaDetectadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            severidad=falla.severidad,
            titulo=falla.titulo,
            descripcion=falla.descripcion,
            requiere_atencion_inmediata=falla.requiere_atencion_inmediata,
            puede_conducir=falla.puede_conducir,
            origen_deteccion="ml",
            sensor_id=falla.sensor_id
        ).emit()
        
        if should_emit_critical_event(falla):
            await FallaCriticaEvent(
                falla_id=falla.id,
                moto_id=falla.moto_id,
                tipo=falla.tipo,
                titulo=falla.titulo,
                descripcion=falla.descripcion,
                puede_conducir=falla.puede_conducir
            ).emit()
        
        return falla


class UpdateFallaUseCase:
    """Caso de uso para actualizar una falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, falla_id: int, data: FallaUpdate) -> Falla:
        """
        Actualiza una falla existente.
        
        Args:
            falla_id: ID de la falla
            data: Datos a actualizar
            
        Returns:
            Falla actualizada
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
            ValueError: Si la actualización no es válida
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar que se puede actualizar
        can_update_falla(falla)
        
        # Actualizar campos
        if data.estado is not None:
            validate_transition_estado(falla.estado, data.estado)
            falla.estado = data.estado
        
        if data.severidad is not None:
            validate_severidad(data.severidad)
            falla.severidad = data.severidad
        
        if data.solucion_aplicada is not None:
            falla.solucion_aplicada = data.solucion_aplicada
        
        if data.costo_real is not None:
            falla.costo_real = data.costo_real
        
        if data.notas_tecnico is not None:
            falla.notas_tecnico = data.notas_tecnico
        
        # Guardar
        falla = await self.repo.update(falla)
        
        return falla


class DiagnosticarFallaUseCase:
    """Caso de uso para diagnosticar una falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        falla_id: int,
        data: FallaDiagnosticar,
        usuario_id: Optional[int] = None
    ) -> Falla:
        """
        Diagnostica una falla.
        
        Args:
            falla_id: ID de la falla
            data: Datos del diagnóstico
            usuario_id: ID del usuario que diagnostica
            
        Returns:
            Falla diagnosticada
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar transición de estado
        validate_transition_estado(falla.estado, EstadoFalla.EN_REVISION.value)
        
        # Actualizar
        falla.estado = EstadoFalla.EN_REVISION.value
        falla.solucion_sugerida = data.solucion_sugerida
        falla.costo_estimado = data.costo_estimado or estimate_costo_reparacion(falla.tipo, falla.severidad)
        falla.fecha_diagnostico = datetime.now(timezone.utc)
        
        if data.notas_tecnico:
            falla.notas_tecnico = data.notas_tecnico
        
        # Guardar
        falla = await self.repo.update(falla)
        
        # Emitir evento
        await FallaDiagnosticadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            solucion_sugerida=falla.solucion_sugerida or "",
            usuario_id=usuario_id,
            costo_estimado=falla.costo_estimado
        ).emit()
        
        return falla


class ResolverFallaUseCase:
    """Caso de uso para resolver una falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        falla_id: int,
        data: FallaResolver,
        usuario_id: Optional[int] = None
    ) -> Falla:
        """
        Marca una falla como resuelta.
        
        Args:
            falla_id: ID de la falla
            data: Datos de la resolución
            usuario_id: ID del usuario que resolvió
            
        Returns:
            Falla resuelta
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar transición
        validate_transition_estado(falla.estado, EstadoFalla.RESUELTA.value)
        
        # Actualizar
        falla.estado = EstadoFalla.RESUELTA.value
        falla.solucion_aplicada = data.solucion_aplicada
        falla.costo_real = data.costo_real
        falla.fecha_resolucion = datetime.now(timezone.utc)
        
        if data.notas_tecnico:
            falla.notas_tecnico = data.notas_tecnico
        
        # Validar fechas
        validate_fechas(
            falla.fecha_deteccion,
            falla.fecha_diagnostico,
            falla.fecha_resolucion
        )
        
        # Calcular días de resolución
        dias_resolucion = calculate_dias_resolucion(
            falla.fecha_deteccion,
            falla.fecha_resolucion  # type: ignore
        )
        
        # Guardar
        falla = await self.repo.update(falla)
        
        # Emitir evento
        await FallaResueltaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            solucion_aplicada=falla.solucion_aplicada or "",
            costo_real=falla.costo_real or 0.0,
            dias_resolucion=dias_resolucion,
            usuario_id=usuario_id
        ).emit()
        
        return falla


class GetFallaUseCase:
    """Caso de uso para obtener una falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, falla_id: int) -> Falla:
        """
        Obtiene una falla por ID.
        
        Args:
            falla_id: ID de la falla
            
        Returns:
            Falla encontrada
            
        Raises:
            ResourceNotFoundException: Si no existe
        """
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        return falla


class ListFallasByMotoUseCase:
    """Caso de uso para listar fallas de una moto."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        filters: FallaFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Falla], int]:
        """
        Lista fallas de una moto con paginación.
        
        Args:
            filters: Filtros a aplicar
            pagination: Parámetros de paginación
            
        Returns:
            Tupla con (lista de fallas, total)
        """
        # Obtener fallas con paginación
        fallas = await self.repo.get_by_moto(
            filters.moto_id,  # type: ignore
            solo_activas=filters.solo_activas or False,
            skip=pagination.offset,
            limit=pagination.limit
        )
        
        # Contar total
        total = await self.repo.count_by_moto(
            filters.moto_id,  # type: ignore
            solo_activas=filters.solo_activas or False
        )
        
        return fallas, total


class GetFallaStatsUseCase:
    """Caso de uso para obtener estadísticas de fallas (Premium)."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, moto_id: int) -> FallaStatsResponse:
        """
        Obtiene estadísticas completas de fallas de una moto.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            Estadísticas de fallas
        """
        # Contar totales
        total_fallas = await self.repo.count_by_moto(moto_id, solo_activas=False)
        fallas_activas = await self.repo.count_by_moto(moto_id, solo_activas=True)
        fallas_resueltas = total_fallas - fallas_activas
        
        # Contar críticas activas
        criticas = await self.repo.get_criticas_activas(moto_id)
        fallas_criticas = len(criticas)
        
        # Stats por categorías
        por_tipo = await self.repo.get_stats_by_tipo(moto_id)
        por_severidad = await self.repo.get_stats_by_severidad(moto_id)
        
        # Estado (calculado manualmente)
        todas_fallas = await self.repo.get_by_moto(moto_id, solo_activas=False, skip=0, limit=10000)
        por_estado = {}
        for falla in todas_fallas:
            por_estado[falla.estado] = por_estado.get(falla.estado, 0) + 1
        
        # Tiempo promedio de resolución
        tiempo_promedio = calcular_tiempo_promedio_resolucion(todas_fallas)
        
        # Costo total
        costo_total = await self.repo.get_costo_total_reparaciones(moto_id)
        
        # Tasa de resolución
        tasa = calcular_tasa_resolucion(total_fallas, fallas_resueltas)
        
        return FallaStatsResponse(
            total_fallas=total_fallas,
            fallas_activas=fallas_activas,
            fallas_resueltas=fallas_resueltas,
            fallas_criticas=fallas_criticas,
            por_tipo=por_tipo,
            por_severidad=por_severidad,
            por_estado=por_estado,
            tiempo_promedio_resolucion_dias=tiempo_promedio,
            costo_total_reparaciones=costo_total,
            tasa_resolucion=tasa
        )


class DeleteFallaUseCase:
    """Caso de uso para eliminar una falla."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, falla_id: int) -> bool:
        """
        Elimina (soft delete) una falla.
        
        Args:
            falla_id: ID de la falla
            
        Returns:
            True si se eliminó
            
        Raises:
            ResourceNotFoundException: Si no existe
        """
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar que se puede eliminar
        from .validators import can_delete_falla
        can_delete_falla(falla)
        
        return await self.repo.delete(falla_id)
