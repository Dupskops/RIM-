"""
Modelos base compartidos para SQLAlchemy.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos SQLAlchemy."""
    pass


class BaseModel(Base):
    """
    Modelo base con campos comunes (timestamps y soft delete).
    Todos los modelos deben heredar de esta clase.
    """
    
    __abstract__ = True
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    def __repr__(self) -> str:
        """Representación string del modelo."""
        return f"<{self.__class__.__name__} {self.id}>"
