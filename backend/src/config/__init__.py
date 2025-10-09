"""
Módulo de configuración de RIM.
Exports centralizados para fácil importación.
"""
from .settings import settings
from .database import (
    Base,  # Importado desde shared/models.py en database.py
    engine,
    AsyncSessionLocal,
    get_db,
    init_db,
    close_db,
)
from .dependencies import (
    get_current_user_id,
    get_current_user,
    get_optional_user,
    require_auth,
    require_admin,
)

__all__ = [
    # Settings
    "settings",
    
    # Database
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "close_db",
    
    # Dependencies
    "get_current_user_id",
    "get_current_user",
    "get_optional_user",
    "require_auth",
    "require_admin",
]