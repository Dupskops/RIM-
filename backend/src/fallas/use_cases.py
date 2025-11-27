"""
Casos de uso para gestión de fallas.
MVP v2.3 - Actualizado para schema simplificado
"""
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.exceptions import (
    ResourceNotFoundException,
    ValidationException
)
from src.shared.base_models import PaginationParams

from .models import Falla, EstadoFalla, SeveridadFalla, OrigenDeteccion
from .repositories import FallaRepository
from .schemas import (
    FallaCreate,
    FallaUpdate,
    FallaFilterParams,
    FallaStatsResponse
)
from .validators import (
    validate_transition_estado,
    validate_falla_data
)
from .services import (
    determine_puede_conducir,
    generate_solucion_sugerida,
    calculate_dias_resolucion,
    can_auto_resolve,
    calculate_prioridad
)
from .events import (
    FallaDetectadaEvent,
    FallaActualizadaEvent,
    FallaResueltaEvent
)


# =============================================================================
# CREAR FALLA (Detección Automática o Reporte Manual)
# =============================================================================

class CreateFallaUseCase:
    """
    Caso de uso para crear una nueva falla.
    
    Flujo según FLUJOS_SISTEMA.md:
    1. Validar datos de entrada
    2. Generar código único FL-YYYYMMDD-NNN
    3. Determinar puede_conducir según tipo y severidad
    4. Generar solución sugerida
    5. Crear registro en DB
    6. Emitir evento FallaDetectada
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
        self.session = session
    
    async def execute(self, data: FallaCreate, usuario_id: int) -> Falla:
        """
        Crea una nueva falla.
        
        Args:
            data: Datos de la falla a crear
            usuario_id: ID del usuario que reporta (0 si es automático)
            
        Returns:
            Falla: Falla creada
            
        Raises:
            ValidationException: Si los datos no son válidos
        """
        # Validar datos
        await validate_falla_data(data, self.session)
        
        # Generar código único
        fecha_actual = datetime.now(timezone.utc)
        codigo_base = f"FL-{fecha_actual.strftime('%Y%m%d')}-"
        
        # Obtener siguiente número secuencial del día
        count_hoy = await self.repo.count_by_date(fecha_actual.date())
        numero_secuencial = str(count_hoy + 1).zfill(3)
        codigo = f"{codigo_base}{numero_secuencial}"
        
        # Determinar si puede conducir
        puede_conducir = determine_puede_conducir(data.tipo, data.severidad)
        
        # Generar solución sugerida
        solucion_sugerida = generate_solucion_sugerida(data.tipo, data.severidad)
        
        # Determinar si requiere atención inmediata
        requiere_atencion_inmediata = (
            data.severidad in [SeveridadFalla.CRITICA, SeveridadFalla.ALTA] or
            not puede_conducir
        )
        
        # Crear falla
        falla = Falla(
            moto_id=data.moto_id,
            componente_id=data.componente_id,
            codigo=codigo,
            tipo=data.tipo.lower(),
            descripcion=data.descripcion,
            severidad=data.severidad,
            estado=EstadoFalla.DETECTADA,
            origen_deteccion=data.origen_deteccion or OrigenDeteccion.SENSOR,
            latitud=data.latitud,
            longitud=data.longitud,
            puede_conducir=puede_conducir,
            requiere_atencion_inmediata=requiere_atencion_inmediata,
            solucion_sugerida=solucion_sugerida,
            fecha_deteccion=fecha_actual
        )
        
        # Guardar
        falla = await self.repo.create(falla)
        
        # Emitir evento
        await FallaDetectadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            componente_id=falla.componente_id,
            tipo=falla.tipo,
            severidad=falla.severidad.value,
            puede_conducir=falla.puede_conducir,
            requiere_atencion_inmediata=falla.requiere_atencion_inmediata,
            usuario_id=usuario_id,
            origen=falla.origen_deteccion.value
        ).emit()
        
        return falla


# =============================================================================
# DIAGNOSTICAR FALLA (Cambiar a EN_REPARACION)
# =============================================================================

class DiagnosticarFallaUseCase:
    """
    Caso de uso para diagnosticar una falla y moverla a reparación.
    
    Flujo según FLUJOS_SISTEMA.md v2.3:
    - Estado: DETECTADA → EN_REPARACION
    - Actualiza solucion_sugerida si se proporciona
    - NO maneja costo_estimado (eso va en mantenimientos)
    - NO maneja fecha_diagnostico (eliminado en v2.3)
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        falla_id: int,
        solucion_sugerida: str,
        usuario_id: int
    ) -> Falla:
        """
        Diagnostica una falla y la mueve a estado EN_REPARACION.
        
        Args:
            falla_id: ID de la falla
            solucion_sugerida: Solución propuesta por técnico/ML
            usuario_id: ID del usuario que diagnostica
            
        Returns:
            Falla: Falla actualizada
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
            ValidationException: Si la transición de estado no es válida
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar transición de estado (DETECTADA → EN_REPARACION)
        validate_transition_estado(falla.estado, EstadoFalla.EN_REPARACION)
        
        # Actualizar
        falla.estado = EstadoFalla.EN_REPARACION
        falla.solucion_sugerida = solucion_sugerida
        
        # Guardar
        falla = await self.repo.update(falla)
        
        # Emitir evento
        await FallaActualizadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            estado_anterior="detectada",
            estado_nuevo="en_reparacion",
            usuario_id=usuario_id
        ).emit()
        
        return falla


# =============================================================================
# RESOLVER FALLA (Cambiar a RESUELTA)
# =============================================================================

class ResolverFallaUseCase:
    """
    Caso de uso para resolver una falla.
    
    Flujo según FLUJOS_SISTEMA.md v2.3:
    - Estado: EN_REPARACION → RESUELTA
    - Registra fecha_resolucion
    - NO maneja solucion_aplicada, costo_real (van en mantenimientos)
    - Calcula días de resolución
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        falla_id: int,
        usuario_id: int
    ) -> Falla:
        """
        Resuelve una falla marcándola como RESUELTA.
        
        Args:
            falla_id: ID de la falla
            usuario_id: ID del usuario que resuelve
            
        Returns:
            Falla: Falla resuelta
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
            ValidationException: Si la transición no es válida
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Validar transición (EN_REPARACION → RESUELTA)
        validate_transition_estado(falla.estado, EstadoFalla.RESUELTA)
        
        # Actualizar
        falla.estado = EstadoFalla.RESUELTA
        falla.fecha_resolucion = datetime.now(timezone.utc)
        
        # Guardar
        falla = await self.repo.update(falla)
        
        # Calcular días de resolución
        dias_resolucion = 0
        if falla.fecha_deteccion and falla.fecha_resolucion:
            dias_resolucion = calculate_dias_resolucion(
                falla.fecha_deteccion,
                falla.fecha_resolucion
            )
        
        # Emitir evento
        await FallaResueltaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            solucion_aplicada="",  # Ya no se maneja en fallas (va en mantenimientos)
            costo_real=0.0,  # Ya no se maneja en fallas (va en mantenimientos)
            dias_resolucion=dias_resolucion,
            usuario_id=usuario_id
        ).emit()
        
        return falla


# =============================================================================
# ACTUALIZAR FALLA (Campos editables)
# =============================================================================

class UpdateFallaUseCase:
    """
    Caso de uso para actualizar campos de una falla.
    
    Campos editables en MVP v2.3:
    - descripcion
    - severidad
    - solucion_sugerida
    - latitud/longitud
    
    NO editables:
    - estado (usar DiagnosticarFalla o ResolverFalla)
    - tipo
    - moto_id, componente_id
    - fechas del sistema
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        falla_id: int,
        data: FallaUpdate,
        usuario_id: int
    ) -> Falla:
        """
        Actualiza campos de una falla.
        
        Args:
            falla_id: ID de la falla
            data: Datos a actualizar
            usuario_id: ID del usuario que actualiza
            
        Returns:
            Falla: Falla actualizada
            
        Raises:
            ResourceNotFoundException: Si la falla no existe
        """
        # Obtener falla
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        # Guardar estado anterior para el evento
        estado_anterior = falla.estado.value
        
        # Actualizar campos permitidos
        if data.descripcion is not None:
            falla.descripcion = data.descripcion
        
        if data.severidad is not None:
            falla.severidad = data.severidad
            # Recalcular puede_conducir
            falla.puede_conducir = determine_puede_conducir(falla.tipo, data.severidad)
            # Recalcular requiere_atencion_inmediata
            falla.requiere_atencion_inmediata = (
                data.severidad in [SeveridadFalla.CRITICA, SeveridadFalla.ALTA] or
                not falla.puede_conducir
            )
        
        if data.solucion_sugerida is not None:
            falla.solucion_sugerida = data.solucion_sugerida
        
        if data.latitud is not None:
            falla.latitud = data.latitud
        
        if data.longitud is not None:
            falla.longitud = data.longitud
        
        # Guardar
        falla = await self.repo.update(falla)
        
        # Emitir evento
        await FallaActualizadaEvent(
            falla_id=falla.id,
            moto_id=falla.moto_id,
            tipo=falla.tipo,
            estado_anterior=estado_anterior,
            estado_nuevo=falla.estado.value,
            usuario_id=usuario_id
        ).emit()
        
        return falla


# =============================================================================
# OBTENER FALLA POR ID
# =============================================================================

class GetFallaByIdUseCase:
    """Caso de uso para obtener una falla por ID."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, falla_id: int) -> Falla:
        """
        Obtiene una falla por ID.
        
        Args:
            falla_id: ID de la falla
            
        Returns:
            Falla: Falla encontrada
            
        Raises:
            ResourceNotFoundException: Si no existe
        """
        falla = await self.repo.get_by_id(falla_id)
        if not falla:
            raise ResourceNotFoundException("Falla", str(falla_id))
        
        return falla


# =============================================================================
# OBTENER FALLA POR CÓDIGO
# =============================================================================

class GetFallaByCodigoUseCase:
    """Caso de uso para obtener una falla por su código único."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, codigo: str) -> Falla:
        """
        Obtiene una falla por código.
        
        Args:
            codigo: Código único (ej: FL-20251110-001)
            
        Returns:
            Falla: Falla encontrada
            
        Raises:
            ResourceNotFoundException: Si no existe
        """
        falla = await self.repo.get_by_codigo(codigo)
        if not falla:
            raise ResourceNotFoundException("Falla", f"codigo={codigo}")
        
        return falla


# =============================================================================
# LISTAR FALLAS DE UNA MOTO
# =============================================================================

class ListFallasByMotoUseCase:
    """Caso de uso para listar fallas de una moto con filtros y paginación."""
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(
        self,
        filters: FallaFilterParams,
        pagination: PaginationParams
    ) -> Tuple[List[Falla], int]:
        """
        Lista fallas de una moto con filtros y paginación.
        
        Args:
            filters: Filtros a aplicar (moto_id, estado, severidad, etc.)
            pagination: Parámetros de paginación (offset, limit)
            
        Returns:
            Tupla con (lista de fallas, total de registros)
        """
        if not filters.moto_id:
            raise ValidationException("moto_id es requerido para listar fallas")
        
        # Aplicar filtros del repository
        fallas = await self.repo.get_by_moto(
            moto_id=filters.moto_id,
            solo_activas=filters.solo_activas or False,
            skip=pagination.offset,
            limit=pagination.limit
        )
        
        # Contar total
        total = await self.repo.count_by_moto(
            moto_id=filters.moto_id,
            solo_activas=filters.solo_activas or False
        )
        
        return fallas, total


# =============================================================================
# OBTENER ESTADÍSTICAS DE FALLAS
# =============================================================================

class GetFallaStatsUseCase:
    """
    Caso de uso para obtener estadísticas de fallas de una moto.
    Feature Premium según FLUJOS_SISTEMA.md
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self, moto_id: int) -> FallaStatsResponse:
        """
        Obtiene estadísticas agregadas de fallas.
        
        Args:
            moto_id: ID de la moto
            
        Returns:
            FallaStatsResponse: Estadísticas calculadas
        """
        # Obtener todas las fallas de la moto
        fallas = await self.repo.get_by_moto(moto_id, solo_activas=False, skip=0, limit=1000)
        
        # Calcular estadísticas
        total = len(fallas)
        activas = sum(1 for f in fallas if f.estado != EstadoFalla.RESUELTA)
        resueltas = sum(1 for f in fallas if f.estado == EstadoFalla.RESUELTA)
        criticas = sum(1 for f in fallas if f.severidad == SeveridadFalla.CRITICA)
        
        # Estadísticas por tipo
        por_tipo: dict = {}
        for falla in fallas:
            por_tipo[falla.tipo] = por_tipo.get(falla.tipo, 0) + 1
        
        # Estadísticas por severidad
        por_severidad: dict = {}
        for falla in fallas:
            key = falla.severidad.value
            por_severidad[key] = por_severidad.get(key, 0) + 1
        
        # Estadísticas por estado
        por_estado: dict = {}
        for falla in fallas:
            key = falla.estado.value
            por_estado[key] = por_estado.get(key, 0) + 1
        
        # Calcular tiempo promedio de resolución (solo fallas resueltas)
        fallas_resueltas = [f for f in fallas if f.estado == EstadoFalla.RESUELTA and f.fecha_deteccion and f.fecha_resolucion]
        
        if fallas_resueltas:
            dias_resolucion = [
                calculate_dias_resolucion(f.fecha_deteccion, f.fecha_resolucion)  # type: ignore
                for f in fallas_resueltas
            ]
            tiempo_promedio_resolucion = sum(dias_resolucion) / len(dias_resolucion)
        else:
            tiempo_promedio_resolucion = 0.0
        
        return FallaStatsResponse(
            total=total,
            activas=activas,
            resueltas=resueltas,
            criticas=criticas,
            por_tipo=por_tipo,
            por_severidad=por_severidad,
            por_estado=por_estado,
            tiempo_promedio_resolucion=tiempo_promedio_resolucion
        )


# =============================================================================
# AUTO-RESOLVER FALLAS TRANSITORIAS
# =============================================================================

class AutoResolveFallasUseCase:
    """
    Caso de uso para auto-resolver fallas transitorias.
    
    Se ejecuta periódicamente (cron job) para resolver automáticamente
    fallas de baja severidad detectadas por sensor que ya no aplican.
    """
    
    def __init__(self, session: AsyncSession):
        self.repo = FallaRepository(session)
    
    async def execute(self) -> int:
        """
        Auto-resuelve fallas transitorias elegibles.
        
        Returns:
            int: Número de fallas auto-resueltas
        """
        # Obtener fallas activas de baja severidad
        fallas_activas = await self.repo.get_by_estado(EstadoFalla.DETECTADA)
        
        resueltas_count = 0
        
        for falla in fallas_activas:
            # Verificar si puede auto-resolverse
            if can_auto_resolve(
                falla.severidad,
                falla.origen_deteccion,
                falla.tipo
            ):
                # Marcar como resuelta
                falla.estado = EstadoFalla.RESUELTA
                falla.fecha_resolucion = datetime.now(timezone.utc)
                falla.solucion_sugerida += " [Auto-resuelta: condición normalizada]"
                
                await self.repo.update(falla)
                resueltas_count += 1
        
        return resueltas_count
