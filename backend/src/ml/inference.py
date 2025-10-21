"""
Motor de inferencia de Machine Learning.

Carga modelos entrenados y realiza predicciones.
"""
import os
import pickle
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Rutas a modelos entrenados
MODELS_DIR = Path(__file__).parent / "trained_models"
FAULT_PREDICTOR_PATH = MODELS_DIR / "fault_predictor.h5"
ANOMALY_DETECTOR_PATH = MODELS_DIR / "anomaly_detector.pkl"


class ModelLoader:
    """Cargador y caché de modelos ML."""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._load_times: Dict[str, datetime] = {}
    
    def load_keras_model(self, model_path: Path, model_name: str) -> Any:
        """
        Carga un modelo de Keras/TensorFlow.
        
        Args:
            model_path: Ruta al archivo .h5
            model_name: Nombre identificador del modelo
            
        Returns:
            Modelo de Keras cargado
        """
        if model_name in self._models:
            logger.info(f"Modelo {model_name} ya está en caché")
            return self._models[model_name]
        
        try:
            # Import lazy para no cargar TensorFlow innecesariamente
            from tensorflow import keras
            
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            model = keras.models.load_model(str(model_path))
            self._models[model_name] = model
            self._load_times[model_name] = datetime.utcnow()
            logger.info(f"Modelo {model_name} cargado exitosamente")
            return model
            
        except Exception as e:
            logger.error(f"Error cargando modelo Keras {model_name}: {e}")
            raise
    
    def load_sklearn_model(self, model_path: Path, model_name: str) -> Any:
        """
        Carga un modelo de scikit-learn.
        
        Args:
            model_path: Ruta al archivo .pkl
            model_name: Nombre identificador del modelo
            
        Returns:
            Modelo de sklearn cargado
        """
        if model_name in self._models:
            logger.info(f"Modelo {model_name} ya está en caché")
            return self._models[model_name]
        
        try:
            if not model_path.exists():
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            self._models[model_name] = model
            self._load_times[model_name] = datetime.utcnow()
            logger.info(f"Modelo {model_name} cargado exitosamente")
            return model
            
        except Exception as e:
            logger.error(f"Error cargando modelo sklearn {model_name}: {e}")
            raise
    
    def get_model(self, model_name: str) -> Optional[Any]:
        """Obtiene un modelo del caché."""
        return self._models.get(model_name)
    
    def reload_model(self, model_name: str, model_path: Path, model_type: str = "keras") -> Any:
        """Recarga un modelo (útil después de reentrenamiento)."""
        if model_name in self._models:
            del self._models[model_name]
        
        if model_type == "keras":
            return self.load_keras_model(model_path, model_name)
        elif model_type == "sklearn":
            return self.load_sklearn_model(model_path, model_name)
        else:
            raise ValueError(f"Tipo de modelo no soportado: {model_type}")


class FaultPredictor:
    """Predictor de fallas usando red neuronal."""
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.model_name = "fault_predictor"
        self.version = "1.0"
        
    def load_model(self):
        """Carga el modelo de predicción de fallas."""
        return self.model_loader.load_keras_model(
            FAULT_PREDICTOR_PATH, 
            self.model_name
        )
    
    def preprocess_input(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        velocidad: float,
        presion_aceite: float,
        kilometraje: int,
        dias_ultimo_mantenimiento: int
    ) -> np.ndarray:
        """
        Preprocesa datos de entrada para el modelo.
        
        Returns:
            Array numpy normalizado listo para predicción
        """
        # Normalización simple (en producción usar scaler guardado)
        features = np.array([[
            temperatura / 150.0,           # Normalizar temperatura (max ~150°C)
            vibracion / 100.0,             # Normalizar vibración (max 100)
            rpm / 15000.0,                 # Normalizar RPM (max ~15000)
            velocidad / 200.0,             # Normalizar velocidad (max ~200 km/h)
            presion_aceite / 10.0,         # Normalizar presión (max ~10 bar)
            kilometraje / 100000.0,        # Normalizar km (normalización por 100k)
            dias_ultimo_mantenimiento / 365.0  # Normalizar días (max 1 año)
        ]])
        
        return features
    
    def predict(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        velocidad: float,
        presion_aceite: float,
        kilometraje: int,
        dias_ultimo_mantenimiento: int
    ) -> Dict[str, Any]:
        """
        Realiza predicción de falla.
        
        Returns:
            Dict con probabilidad de falla y metadata
        """
        try:
            model = self.load_model()
            
            # Preprocesar entrada
            X = self.preprocess_input(
                temperatura, vibracion, rpm, velocidad,
                presion_aceite, kilometraje, dias_ultimo_mantenimiento
            )
            
            # Realizar predicción
            prediction = model.predict(X, verbose=0)
            probabilidad_falla = float(prediction[0][0])
            
            # Calcular tiempo estimado hasta falla (días)
            tiempo_estimado = self._calcular_tiempo_estimado(
                probabilidad_falla,
                dias_ultimo_mantenimiento,
                kilometraje
            )
            
            # Determinar tipo de falla más probable
            tipo_falla = self._determinar_tipo_falla(
                temperatura, vibracion, rpm, presion_aceite
            )
            
            return {
                "probabilidad_falla": probabilidad_falla,
                "confianza": probabilidad_falla,  # En este modelo, confianza = probabilidad
                "tiempo_estimado_dias": tiempo_estimado,
                "fecha_estimada": datetime.utcnow() + timedelta(days=tiempo_estimado) if tiempo_estimado else None,
                "tipo_falla_probable": tipo_falla,
                "severidad": self._calcular_severidad(probabilidad_falla),
                "inputs": {
                    "temperatura": temperatura,
                    "vibracion": vibracion,
                    "rpm": rpm,
                    "velocidad": velocidad,
                    "presion_aceite": presion_aceite,
                    "kilometraje": kilometraje,
                    "dias_ultimo_mantenimiento": dias_ultimo_mantenimiento
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de falla: {e}")
            raise
    
    def _calcular_tiempo_estimado(
        self,
        probabilidad: float,
        dias_ultimo_mant: int,
        kilometraje: int
    ) -> Optional[int]:
        """Calcula tiempo estimado hasta falla en días."""
        if probabilidad < 0.3:
            return None  # Probabilidad muy baja
        
        # Fórmula empírica (ajustar según datos reales)
        base_dias = 90  # 3 meses base
        factor_prob = (1 - probabilidad) * base_dias
        factor_mant = max(0, 30 - dias_ultimo_mant * 0.1)
        
        tiempo = int(factor_prob + factor_mant)
        return max(1, tiempo)  # Mínimo 1 día
    
    def _determinar_tipo_falla(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        presion_aceite: float
    ) -> str:
        """Determina tipo de falla más probable basado en sensores."""
        if temperatura > 110:
            return "sobrecalentamiento_motor"
        if vibracion > 70:
            return "desbalance_ruedas"
        if presion_aceite < 2.0:
            return "sistema_lubricacion"
        if rpm > 12000:
            return "revoluciones_excesivas"
        return "desgaste_general"
    
    def _calcular_severidad(self, probabilidad: float) -> str:
        """Calcula severidad de la falla."""
        if probabilidad >= 0.85:
            return "critica"
        elif probabilidad >= 0.7:
            return "alta"
        elif probabilidad >= 0.5:
            return "media"
        else:
            return "baja"


class AnomalyDetector:
    """Detector de anomalías usando aislamiento o clustering."""
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
        self.model_name = "anomaly_detector"
        self.version = "1.0"
    
    def load_model(self):
        """Carga el modelo de detección de anomalías."""
        return self.model_loader.load_sklearn_model(
            ANOMALY_DETECTOR_PATH,
            self.model_name
        )
    
    def preprocess_input(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        velocidad: float,
        presion_aceite: float,
        nivel_combustible: float
    ) -> np.ndarray:
        """Preprocesa datos para detección de anomalías."""
        features = np.array([[
            temperatura,
            vibracion,
            rpm,
            velocidad,
            presion_aceite,
            nivel_combustible
        ]])
        return features
    
    def detect(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        velocidad: float,
        presion_aceite: float,
        nivel_combustible: float
    ) -> Dict[str, Any]:
        """
        Detecta anomalías en datos de sensores.
        
        Returns:
            Dict con resultado de detección y scores
        """
        try:
            model = self.load_model()
            
            # Preprocesar
            X = self.preprocess_input(
                temperatura, vibracion, rpm, velocidad,
                presion_aceite, nivel_combustible
            )
            
            # Predecir (-1 = anomalía, 1 = normal)
            prediction = model.predict(X)
            es_anomalia = prediction[0] == -1
            
            # Obtener score de anomalía
            scores = model.score_samples(X)
            anomaly_score = float(scores[0])
            
            # Confianza (normalizada entre 0 y 1)
            confianza = self._calcular_confianza(anomaly_score)
            
            # Identificar sensores anómalos
            sensores_anomalos = self._identificar_sensores_anomalos(
                temperatura, vibracion, rpm, velocidad,
                presion_aceite, nivel_combustible
            )
            
            return {
                "es_anomalia": es_anomalia,
                "confianza": confianza,
                "anomaly_score": anomaly_score,
                "sensores_anomalos": sensores_anomalos,
                "tipo_anomalia": self._clasificar_anomalia(sensores_anomalos),
                "severidad": self._calcular_severidad_anomalia(confianza, len(sensores_anomalos)),
                "inputs": {
                    "temperatura": temperatura,
                    "vibracion": vibracion,
                    "rpm": rpm,
                    "velocidad": velocidad,
                    "presion_aceite": presion_aceite,
                    "nivel_combustible": nivel_combustible
                }
            }
            
        except Exception as e:
            logger.error(f"Error en detección de anomalía: {e}")
            raise
    
    def _calcular_confianza(self, score: float) -> float:
        """Convierte score de anomalía a confianza [0, 1]."""
        # Normalización empírica (ajustar según modelo)
        # Scores más negativos = mayor anomalía
        confianza = 1.0 / (1.0 + np.exp(score))  # Función sigmoide
        return float(np.clip(confianza, 0.0, 1.0))
    
    def _identificar_sensores_anomalos(
        self,
        temperatura: float,
        vibracion: float,
        rpm: int,
        velocidad: float,
        presion_aceite: float,
        nivel_combustible: float
    ) -> List[str]:
        """Identifica qué sensores están fuera de rango."""
        anomalos = []
        
        # Rangos normales (ajustar según datos históricos)
        if temperatura > 120 or temperatura < 30:
            anomalos.append("temperatura")
        if vibracion > 80:
            anomalos.append("vibracion")
        if rpm > 13000:
            anomalos.append("rpm")
        if velocidad > 180:
            anomalos.append("velocidad")
        if presion_aceite < 1.5 or presion_aceite > 8:
            anomalos.append("presion_aceite")
        if nivel_combustible < 5:
            anomalos.append("nivel_combustible")
        
        return anomalos
    
    def _clasificar_anomalia(self, sensores_anomalos: List[str]) -> str:
        """Clasifica tipo de anomalía según sensores."""
        if not sensores_anomalos:
            return "leve"
        
        if "temperatura" in sensores_anomalos:
            return "termica"
        if "presion_aceite" in sensores_anomalos:
            return "lubricacion"
        if "vibracion" in sensores_anomalos:
            return "mecanica"
        if "rpm" in sensores_anomalos or "velocidad" in sensores_anomalos:
            return "operacional"
        
        return "multiple"
    
    def _calcular_severidad_anomalia(self, confianza: float, num_sensores: int) -> str:
        """Calcula severidad de anomalía."""
        if confianza > 0.9 and num_sensores >= 3:
            return "critica"
        elif confianza > 0.75 and num_sensores >= 2:
            return "alta"
        elif confianza > 0.6:
            return "media"
        else:
            return "baja"


# Instancia global del cargador de modelos
model_loader = ModelLoader()

# Instancias globales de predictores
fault_predictor = FaultPredictor(model_loader)
anomaly_detector = AnomalyDetector(model_loader)
