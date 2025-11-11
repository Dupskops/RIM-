from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Moto, EstadoActual, ReglaEstado, EstadoSalud, LogicaRegla
from .repositories import ComponenteRepository, EstadoActualRepository, ReglaEstadoRepository
from .events import emit_estado_cambiado, emit_estado_critico_detectado, emit_servicio_vencido


class MotoService:
    
    @staticmethod
    def prepare_moto_data(moto_dict: Dict[str, Any], usuario_id: int) -> Dict[str, Any]:
        """Prepara datos de moto normalizando campos de texto."""
        if "vin" in moto_dict and moto_dict["vin"]:
            moto_dict["vin"] = str(moto_dict["vin"]).strip().upper()
        if "placa" in moto_dict and moto_dict["placa"]:
            moto_dict["placa"] = str(moto_dict["placa"]).strip().upper()
        moto_dict["usuario_id"] = usuario_id
        return moto_dict
    
    @staticmethod
    def verify_ownership(moto: Moto, usuario_id: int) -> bool:
        return moto.usuario_id == usuario_id
    
    @staticmethod
    def evaluar_estado(valor: Decimal, regla: ReglaEstado) -> EstadoSalud:
        if regla.logica == LogicaRegla.MAYOR_QUE:
            if regla.limite_critico and valor >= regla.limite_critico:
                return EstadoSalud.CRITICO
            elif regla.limite_atencion and valor >= regla.limite_atencion:
                return EstadoSalud.ATENCION
            elif regla.limite_bueno and valor >= regla.limite_bueno:
                return EstadoSalud.BUENO
            else:
                return EstadoSalud.EXCELENTE
        elif regla.logica == LogicaRegla.MENOR_QUE:
            if regla.limite_critico and valor <= regla.limite_critico:
                return EstadoSalud.CRITICO
            elif regla.limite_atencion and valor <= regla.limite_atencion:
                return EstadoSalud.ATENCION
            elif regla.limite_bueno and valor <= regla.limite_bueno:
                return EstadoSalud.BUENO
            else:
                return EstadoSalud.EXCELENTE
        elif regla.logica == LogicaRegla.ENTRE:
            return EstadoSalud.BUENO
        return EstadoSalud.BUENO
    
    @staticmethod
    def calcular_estado_general(estados: List[EstadoActual]) -> EstadoSalud:
        if not estados:
            return EstadoSalud.EXCELENTE
        prioridad = {
            EstadoSalud.CRITICO: 4,
            EstadoSalud.ATENCION: 3,
            EstadoSalud.BUENO: 2,
            EstadoSalud.EXCELENTE: 1
        }
        peor_estado = EstadoSalud.EXCELENTE
        peor_prioridad = 1
        for estado in estados:
            p = prioridad.get(estado.estado, 1)
            if p > peor_prioridad:
                peor_prioridad = p
                peor_estado = estado.estado
        return peor_estado
    
    @staticmethod
    async def check_servicio_vencido(moto: Moto, kilometraje_anterior: Decimal) -> None:
        """Verifica si se debe emitir evento de servicio vencido según kilometraje."""
        INTERVALO_SERVICIO = Decimal("5000.0")
        anterior_int = int(kilometraje_anterior // INTERVALO_SERVICIO)
        actual_int = int(moto.kilometraje_actual // INTERVALO_SERVICIO)
        if actual_int > anterior_int:
            await emit_servicio_vencido(
                moto_id=moto.id,  # PK actualizado en v2.3: moto_id → id
                kilometraje_actual=float(moto.kilometraje_actual),
                tipo_servicio="mantenimiento_programado"
            )
    
    @staticmethod
    async def handle_estado_change(
        moto_id: int,
        componente_id: int,
        estado_anterior: Optional[EstadoSalud],
        estado_nuevo: EstadoSalud,
        valor_actual: Decimal
    ) -> None:
        """Maneja cambios de estado y emite eventos correspondientes."""
        if estado_anterior and estado_anterior != estado_nuevo:
            await emit_estado_cambiado(
                moto_id=moto_id,
                componente_id=componente_id,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo
            )
        if estado_nuevo == EstadoSalud.CRITICO:
            await emit_estado_critico_detectado(
                moto_id=moto_id,
                componente_id=componente_id,
                valor_actual=float(valor_actual)
            )
    
    @staticmethod
    async def procesar_lectura_y_actualizar_estado(
        db: AsyncSession,
        moto_id: int,
        componente_id: int,
        parametro_id: int,
        valor: Decimal
    ) -> EstadoActual:
        """
        Procesa una lectura de sensor y actualiza el estado actual del componente.
        
        Esta función es llamada desde el módulo de sensores cuando se crea una nueva lectura.
        Evalúa las reglas de estado y actualiza el estado_actual correspondiente.
        
        Args:
            db: Sesión de base de datos
            moto_id: ID de la moto
            componente_id: ID del componente
            parametro_id: ID del parámetro medido
            valor: Valor de la lectura
            
        Returns:
            EstadoActual actualizado o creado
        """
        regla_repo = ReglaEstadoRepository(db)
        estado_repo = EstadoActualRepository(db)
        
        # 1. Obtener regla aplicable para este componente-parámetro
        regla = await regla_repo.get_by_componente_parametro(componente_id, parametro_id)
        
        if not regla:
            # Si no hay regla, asignar estado BUENO por defecto
            nuevo_estado = EstadoSalud.BUENO
        else:
            # 2. Evaluar estado según la regla
            nuevo_estado = MotoService.evaluar_estado(valor, regla)
        
        # 3. Obtener estado actual anterior (si existe)
        estado_anterior_obj = await estado_repo.get_by_componente(moto_id, componente_id)
        estado_anterior = estado_anterior_obj.estado if estado_anterior_obj else None
        
        # 4. Actualizar estado_actual (upsert)
        estado_actualizado = await estado_repo.upsert_estado_actual(
            moto_id=moto_id,
            componente_id=componente_id,
            ultimo_valor=valor,
            estado=nuevo_estado
        )
        
        # 5. Emitir eventos si hay cambio de estado
        await MotoService.handle_estado_change(
            moto_id=moto_id,
            componente_id=componente_id,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            valor_actual=valor
        )
        
        return estado_actualizado
    
    @staticmethod
    async def provision_estados_iniciales(
        db: AsyncSession,
        moto_id: int,
        modelo_moto_id: int
    ) -> None:
        """
        Crea registros iniciales en estado_actual para todos los componentes del modelo.
        
        Llamado al registrar una nueva moto. Crea un estado inicial BUENO para cada
        componente del modelo (11 componentes para KTM 390 Duke 2024).
        
        Args:
            db: Sesión de base de datos
            moto_id: ID de la moto recién creada
            modelo_moto_id: ID del modelo de moto
        """
        componente_repo = ComponenteRepository(db)
        estado_repo = EstadoActualRepository(db)
        
        # Obtener todos los componentes del modelo
        componentes = await componente_repo.list_by_modelo(modelo_moto_id)
        
        # Crear estados iniciales en lote
        estados_iniciales: List[Dict[str, Any]] = [
            {
                "moto_id": moto_id,
                "componente_id": componente.id,
                "ultimo_valor": None,  # Sin lecturas aún
                "estado": EstadoSalud.BUENO,  # Estado inicial optimista
                "ultima_actualizacion": datetime.now()
            }
            for componente in componentes
        ]
        
        await estado_repo.create_bulk(estados_iniciales)
