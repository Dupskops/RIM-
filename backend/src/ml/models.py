"""
Modelos de base de datos para el módulo de ML (Machine Learning).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from src.shared.models import BaseModel


class TipoPrediccion(str, enum.Enum):
    """Tipos de predicciones del sistema."""
    FALLA = "falla"
    ANOMALIA = "anomalia"
    MANTENIMIENTO = "mantenimiento"
    DESGASTE = "desgaste"


class NivelConfianza(str, enum.Enum):
    """Niveles de confianza en las predicciones."""
    MUY_BAJO = "muy_bajo"  # < 50%
    BAJO = "bajo"          # 50-70%
    MEDIO = "medio"        # 70-85%
    ALTO = "alto"          # 85-95%
    MUY_ALTO = "muy_alto"  # > 95%


class EstadoPrediccion(str, enum.Enum):
    """Estados de una predicción."""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    FALSA = "falsa"
    EXPIRADA = "expirada"


class Prediccion(BaseModel):
    """
    Modelo de predicción generada por ML.
    
    Almacena predicciones de fallas, anomalías, mantenimiento, etc.
    generadas por los modelos de Machine Learning.
    """
    __tablename__ = "predicciones"
    
    # Relaciones
    moto_id = Column(Integer, ForeignKey("motos.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    
    # Información de la predicción
    tipo = Column(String(50), nullable=False, index=True)
    descripcion = Column(Text, nullable=False)
    
    # Confianza y probabilidad
    confianza = Column(Float, nullable=False)  # 0.0 - 1.0
    nivel_confianza = Column(String(20), nullable=False)
    probabilidad_falla = Column(Float, nullable=True)  # 0.0 - 1.0
    
    # Tiempo estimado
    tiempo_estimado_dias = Column(Integer, nullable=True)  # Días hasta falla estimada
    fecha_estimada = Column(DateTime, nullable=True)
    
    # Metadata del modelo
    modelo_usado = Column(String(100), nullable=False)
    version_modelo = Column(String(20), nullable=False)
    
    # Datos de entrada que generaron la predicción
    datos_entrada = Column(JSONB, nullable=False)
    
    # Resultados detallados
    resultados = Column(JSONB, nullable=False)  # Salida completa del modelo
    metricas = Column(JSONB, nullable=True)     # Métricas adicionales
    
    # Estado y validación
    estado = Column(String(20), nullable=False, default=EstadoPrediccion.PENDIENTE.value)
    validada = Column(Boolean, default=False)
    validada_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    validada_en = Column(DateTime, nullable=True)
    
    # Referencias
    falla_relacionada_id = Column(Integer, ForeignKey("fallas.id"), nullable=True)
    mantenimiento_relacionado_id = Column(Integer, ForeignKey("mantenimientos.id"), nullable=True)
    
    # Notificación
    notificacion_enviada = Column(Boolean, default=False)
    
    @property
    def nivel_confianza_valor(self) -> NivelConfianza:
        """Obtiene el nivel de confianza como enum."""
        if self.confianza < 0.5:
            return NivelConfianza.MUY_BAJO
        elif self.confianza < 0.7:
            return NivelConfianza.BAJO
        elif self.confianza < 0.85:
            return NivelConfianza.MEDIO
        elif self.confianza < 0.95:
            return NivelConfianza.ALTO
        else:
            return NivelConfianza.MUY_ALTO
    
    @property
    def es_critica(self) -> bool:
        """Determina si la predicción es crítica."""
        return (
            self.confianza >= 0.85 and
            self.tipo in [TipoPrediccion.FALLA.value, TipoPrediccion.ANOMALIA.value]
        )
    
    def marcar_como_confirmada(self):
        """Marca la predicción como confirmada."""
        self.estado = EstadoPrediccion.CONFIRMADA.value
        self.validada = True
    
    def marcar_como_falsa(self):
        """Marca la predicción como falsa."""
        self.estado = EstadoPrediccion.FALSA.value
        self.validada = True


class EntrenamientoModelo(BaseModel):
    """
    Modelo para registrar entrenamientos de modelos ML.
    
    Almacena información sobre entrenamientos, métricas de performance
    y metadatos del modelo entrenado.
    """
    __tablename__ = "entrenamientos_modelos"
    
    # Información del modelo
    nombre_modelo = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    tipo_modelo = Column(String(50), nullable=False)  # clasificacion, regresion, clustering
    
    # Métricas de entrenamiento
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    mse = Column(Float, nullable=True)  # Mean Squared Error
    rmse = Column(Float, nullable=True)  # Root Mean Squared Error
    
    # Datos de entrenamiento
    num_muestras_entrenamiento = Column(Integer, nullable=False)
    num_muestras_validacion = Column(Integer, nullable=False)
    num_muestras_test = Column(Integer, nullable=False)
    
    # Configuración
    hiperparametros = Column(JSONB, nullable=False)
    features_usadas = Column(JSONB, nullable=False)  # Lista de features
    
    # Metadata
    duracion_entrenamiento_segundos = Column(Float, nullable=True)
    fecha_inicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)
    
    # Archivos
    ruta_modelo = Column(String(255), nullable=False)
    ruta_scaler = Column(String(255), nullable=True)
    
    # Estado
    en_produccion = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    
    # Usuario que entrenó
    entrenado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Notas
    notas = Column(Text, nullable=True)
    
    @property
    def es_mejor_que_anterior(self) -> bool:
        """Determina si este modelo es mejor que versiones anteriores."""
        # Lógica simplificada: accuracy > 0.9 o f1_score > 0.85
        if self.accuracy and self.accuracy > 0.9:
            return True
        if self.f1_score and self.f1_score > 0.85:
            return True
        return False
