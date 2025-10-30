from decimal import Decimal
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP, Numeric, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from src.shared.models import Base


class LogicaRegla(str, enum.Enum):
    MAYOR_QUE = "MAYOR_QUE"
    MENOR_QUE = "MENOR_QUE"
    ENTRE = "ENTRE"


class EstadoSalud(str, enum.Enum):
    EXCELENTE = "EXCELENTE"
    BUENO = "BUENO"
    ATENCION = "ATENCION"
    CRITICO = "CRITICO"


class Moto(Base):
    __tablename__ = "motos"
    
    moto_id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    vin = Column(String(17), unique=True, nullable=True, index=True)
    modelo = Column(String(100), nullable=False, default="KTM 390 Duke")
    ano = Column(Integer, nullable=False)
    placa = Column(String(20), unique=True, nullable=True, index=True)
    color = Column(String(50), nullable=True)
    kilometraje_actual = Column(Numeric(10, 2), nullable=False, default=0.0)
    observaciones = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()", onupdate="now()")
    
    usuario = relationship("Usuario", back_populates="motos")
    historial_lecturas = relationship("HistorialLectura", back_populates="moto", cascade="all, delete-orphan")
    estado_actual = relationship("EstadoActual", back_populates="moto", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Moto {self.modelo} VIN={self.vin}>"


class Componente(Base):
    __tablename__ = "componentes"
    
    componente_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    mesh_id_3d = Column(String(100), unique=True, nullable=True)
    descripcion = Column(Text, nullable=True)
    
    reglas_estado = relationship("ReglaEstado", back_populates="componente", cascade="all, delete-orphan")
    estado_actual = relationship("EstadoActual", back_populates="componente", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Componente {self.nombre}>"


class Parametro(Base):
    __tablename__ = "parametros"
    
    parametro_id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    unidad_medida = Column(String(20), nullable=True)
    
    reglas_estado = relationship("ReglaEstado", back_populates="parametro", cascade="all, delete-orphan")
    historial_lecturas = relationship("HistorialLectura", back_populates="parametro")
    
    def __repr__(self):
        return f"<Parametro {self.nombre} ({self.unidad_medida})>"


class ReglaEstado(Base):
    __tablename__ = "reglas_estado"
    __table_args__ = (
        UniqueConstraint('componente_id', 'parametro_id', name='uq_componente_parametro'),
    )
    
    regla_id = Column(Integer, primary_key=True, index=True)
    componente_id = Column(Integer, ForeignKey("componentes.componente_id", ondelete="CASCADE"), nullable=False, index=True)
    parametro_id = Column(Integer, ForeignKey("parametros.parametro_id", ondelete="CASCADE"), nullable=False, index=True)
    logica = Column(SQLEnum(LogicaRegla, name="logica_regla"), nullable=False)
    limite_bueno = Column(Numeric(10, 2), nullable=True)
    limite_atencion = Column(Numeric(10, 2), nullable=True)
    limite_critico = Column(Numeric(10, 2), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default="now()", onupdate="now()")
    
    componente = relationship("Componente", back_populates="reglas_estado")
    parametro = relationship("Parametro", back_populates="reglas_estado")
    
    def __repr__(self):
        return f"<ReglaEstado componente={self.componente_id} parametro={self.parametro_id}>"


class HistorialLectura(Base):
    __tablename__ = "historial_lecturas"
    
    lectura_id = Column(Integer, primary_key=True, index=True)
    moto_id = Column(Integer, ForeignKey("motos.moto_id", ondelete="CASCADE"), nullable=False, index=True)
    parametro_id = Column(Integer, ForeignKey("parametros.parametro_id", ondelete="RESTRICT"), nullable=False, index=True)
    valor = Column(Numeric(10, 3), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    moto = relationship("Moto", back_populates="historial_lecturas")
    parametro = relationship("Parametro", back_populates="historial_lecturas")
    
    def __repr__(self):
        return f"<Lectura moto={self.moto_id} param={self.parametro_id} valor={self.valor}>"


class EstadoActual(Base):
    __tablename__ = "estado_actual"
    __table_args__ = (
        UniqueConstraint('moto_id', 'componente_id', name='uq_moto_componente'),
    )
    
    estado_actual_id = Column(Integer, primary_key=True, index=True)
    moto_id = Column(Integer, ForeignKey("motos.moto_id", ondelete="CASCADE"), nullable=False, index=True)
    componente_id = Column(Integer, ForeignKey("componentes.componente_id", ondelete="CASCADE"), nullable=False)
    ultimo_valor = Column(Numeric(10, 3), nullable=True)
    estado = Column(SQLEnum(EstadoSalud, name="estado_salud"), nullable=False)
    ultima_actualizacion = Column(TIMESTAMP(timezone=True), nullable=False)
    
    moto = relationship("Moto", back_populates="estado_actual")
    componente = relationship("Componente", back_populates="estado_actual")
    
    def __repr__(self):
        return f"<EstadoActual moto={self.moto_id} componente={self.componente_id} estado={self.estado.value}>"
