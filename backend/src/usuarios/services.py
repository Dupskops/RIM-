"""
Servicios para gestión de usuarios.
Lógica de negocio para operaciones de usuarios.
"""
from typing import Dict, Any
from datetime import datetime

from src.auth.services import password_service


class UsuarioService:
    """Servicio para operaciones de usuario."""
    
    @staticmethod
    def prepare_usuario_data(
        email: str,
        password: str,
        nombre: str,
        telefono: str | None = None,
        es_admin: bool = False,
        activo: bool = True
    ) -> Dict[str, Any]:
        """
        Prepara datos de usuario para creación.
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            nombre: Nombre completo
            telefono: Teléfono (opcional)
            es_admin: Si es administrador
            activo: Si está activo
            
        Returns:
            Diccionario con datos preparados
        """
        return {
            "email": email,
            "password_hash": password_service.hash_password(password),
            "nombre": nombre,
            "telefono": telefono,
            "email_verificado": False,  # Por defecto no verificado
            "es_admin": es_admin,
            "activo": activo,
        }
    
    @staticmethod
    def calculate_pagination(
        page: int,
        page_size: int,
        total: int
    ) -> Dict[str, int]:
        """
        Calcula valores de paginación.
        
        Args:
            page: Número de página (1-indexed)
            page_size: Tamaño de página
            total: Total de elementos
            
        Returns:
            Diccionario con skip, limit, total_pages
        """
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size  # Redondeo hacia arriba
        
        return {
            "skip": skip,
            "limit": page_size,
            "total_pages": total_pages
        }


# Instancia singleton del servicio
usuario_service = UsuarioService()
