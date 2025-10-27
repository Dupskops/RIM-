"""
Servicios de lógica de negocio para motos.
"""
from typing import Optional
from datetime import datetime
import math

from .schemas import MotoResponse, UsuarioBasicInfo
from .models import Moto, MotoComponente
from ..auth.models import Usuario


class MotoService:
    """Servicio con lógica de negocio para motos."""
    
    @staticmethod
    def prepare_moto_data(moto_dict: dict, usuario_id: int) -> dict:
        """
        Prepara los datos de una moto para creación.
        
        Args:
            moto_dict: Diccionario con datos de la moto
            usuario_id: ID del usuario propietario
            
        Returns:
            Diccionario con datos preparados
        """
        # Normalizar VIN y placa a mayúsculas
        if "vin" in moto_dict:
            moto_dict["vin"] = moto_dict["vin"].upper()
        
        if "placa" in moto_dict and moto_dict["placa"]:
            moto_dict["placa"] = moto_dict["placa"].upper()
        
        # Establecer marca como KTM
        moto_dict["marca"] = "KTM"
        
        # Asignar usuario
        moto_dict["usuario_id"] = usuario_id
        
        return moto_dict
    
    @staticmethod
    def validate_kilometraje_update(current_km: int, new_km: int) -> tuple[bool, Optional[str]]:
        """
        Valida que el nuevo kilometraje sea mayor o igual al actual.
        
        Args:
            current_km: Kilometraje actual
            new_km: Nuevo kilometraje
            
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        if new_km < current_km:
            return False, "El nuevo kilometraje no puede ser menor al actual"
        
        # Validar que no haya un salto sospechoso (más de 100,000 km)
        diff = new_km - current_km
        if diff > 100000:
            return False, "El incremento de kilometraje parece sospechoso (más de 100,000 km)"
        
        return True, None
    
    @staticmethod
    def verify_ownership(moto: Moto, usuario_id: int) -> bool:
        """
        Verifica que el usuario sea el propietario de la moto.
        
        Args:
            moto: Moto a verificar
            usuario_id: ID del usuario
            
        Returns:
            True si es propietario, False si no
        """
        return moto.usuario_id == usuario_id
    
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
    def build_moto_response(moto: Moto) -> dict:
        """
        Construye el diccionario de respuesta para una moto.
        
        Args:
            moto: Moto a convertir
            
        Returns:
            Diccionario con datos de la moto
        """
        moto_dict = {
            "id": moto.id,
            "usuario_id": moto.usuario_id,
            "marca": moto.marca,
            "modelo": moto.modelo,
            "año": moto.año,
            "vin": moto.vin,
            "placa": moto.placa,
            "color": moto.color,
            "kilometraje": moto.kilometraje,
            "observaciones": moto.observaciones,
            "created_at": moto.created_at,
            "updated_at": moto.updated_at,
            "deleted_at": moto.deleted_at,
            "nombre_completo": moto.nombre_completo,
            "es_ktm": moto.es_ktm,
        }
        
        # Incluir información del usuario si está cargado
        if moto.usuario:
            moto_dict["usuario"] = {
                "id": moto.usuario.id,
                "nombre": moto.usuario.nombre,
                "apellido": getattr(moto.usuario, "apellido", None),
                "email": moto.usuario.email
            }
        
        return moto_dict

    # ---------------- Componente helpers ----------------
    @staticmethod
    def prepare_componente_data(componente_dict: dict, moto_id: int) -> dict:
        componente_dict["moto_id"] = moto_id
        return componente_dict

    @staticmethod
    def build_componente_response(componente: MotoComponente) -> dict:
        return {
            "id": componente.id,
            "moto_id": componente.moto_id,
            "tipo": componente.tipo,
            "nombre": componente.nombre,
            "component_state": componente.component_state.value if componente.component_state is not None else None,
            "last_updated": componente.last_updated,
            "extra_data": componente.extra_data,
        }
