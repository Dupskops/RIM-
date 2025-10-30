from typing import Optional, List
from decimal import Decimal
from .models import Moto, EstadoActual, ReglaEstado, EstadoSalud, LogicaRegla
from .events import emit_estado_cambiado, emit_estado_critico_detectado, emit_servicio_vencido


class MotoService:
    
    @staticmethod
    def prepare_moto_data(moto_dict: dict, usuario_id: int) -> dict:
        if "vin" in moto_dict and moto_dict["vin"]:
            moto_dict["vin"] = moto_dict["vin"].strip().upper()
        if "placa" in moto_dict and moto_dict["placa"]:
            moto_dict["placa"] = moto_dict["placa"].strip().upper()
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
        INTERVALO_SERVICIO = Decimal("5000.0")
        anterior_int = int(kilometraje_anterior // INTERVALO_SERVICIO)
        actual_int = int(moto.kilometraje_actual // INTERVALO_SERVICIO)
        if actual_int > anterior_int:
            await emit_servicio_vencido(
                moto_id=moto.moto_id,
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
