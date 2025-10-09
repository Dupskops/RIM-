"""
Configuración de base de datos con SQLAlchemy (async).
Proporciona session factory y base para modelos.
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import text
from typing import AsyncGenerator
import logging

from .settings import settings
from src.shared.models import Base  # Importar Base desde shared/models

logger = logging.getLogger(__name__)

# ============================================
# ENGINE ASÍNCRONO
# ============================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
)

# ============================================
# SESSION FACTORY
# ============================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ============================================
# BASE YA IMPORTADA DESDE shared/models.py
# No redefinir aquí: Base ya está disponible
# ============================================


# ============================================
# DEPENDENCY PARA FASTAPI
# ============================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de base de datos para endpoints FastAPI.
    
    Uso:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================
# INICIALIZACIÓN DE BASE DE DATOS
# ============================================
async def init_db():
    """
    Crea todas las tablas en la base de datos.
    Solo usar en desarrollo. En producción usar Alembic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Cierra todas las conexiones del pool."""
    await engine.dispose()


async def check_db_connection() -> bool:
    """
    Verifica que la conexión a la base de datos esté funcionando.
    
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error verificando conexión a DB: {e}")
        return False