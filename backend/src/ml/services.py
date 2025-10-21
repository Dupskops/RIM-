"""
Servicios del módulo de ML.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.ml.repositories import PrediccionRepository, EntrenamientoRepository
from src.ml.inference import fault_predictor, anomaly_detector
from src.ml.validators import (
    validar_datos_prediccion,
    validar_datos_anomalia,
    es_prediccion_valida
)
from src.ml.models import Prediccion, EntrenamientoModelo
from src.ml.schemas import DatosSensor

logger = logging.getLogger(__name__)


class MLService:
    """Servicio principal de Machine Learning."""
    
    def __init__(
        self,
        prediccion_repo: PrediccionRepository,
        entrenamiento_repo: EntrenamientoRepository
    ):
        self.prediccion_repo = prediccion_repo
        self.entrenamiento_repo = entrenamiento_repo
    
    async def predecir_falla(
        self,
        db,
        moto_id: int,
        usuario_id: int,
        datos_sensor: DatosSensor,
        kilometraje: int,
        dias_ultimo_mantenimiento: int
    ) -> Prediccion:
        """
        Realiza predicción de falla usando el modelo de ML.
        
        Args:
            db: Sesión de base de datos
            moto_id: ID de la motocicleta
            usuario_id: ID del usuario propietario
            datos_sensor: Datos de sensores
            kilometraje: Kilometraje actual
            dias_ultimo_mantenimiento: Días desde último mantenimiento
            
        Returns:
            Predicción creada
        """
        # Validar datos
        es_valido, errores = validar_datos_prediccion(
            temperatura=datos_sensor.temperatura or 0,
            vibracion=datos_sensor.vibracion or 0,
            rpm=datos_sensor.rpm or 0,
            velocidad=datos_sensor.velocidad or 0,
            presion_aceite=datos_sensor.presion_aceite or 0,
            kilometraje=kilometraje,
            dias_ultimo_mantenimiento=dias_ultimo_mantenimiento
        )
        
        if not es_valido:
            logger.warning(f"Datos de predicción con advertencias: {errores}")
        
        # Realizar predicción con el modelo
        resultado = fault_predictor.predict(
            temperatura=datos_sensor.temperatura or 0,
            vibracion=datos_sensor.vibracion or 0,
            rpm=datos_sensor.rpm or 0,
            velocidad=datos_sensor.velocidad or 0,
            presion_aceite=datos_sensor.presion_aceite or 0,
            kilometraje=kilometraje,
            dias_ultimo_mantenimiento=dias_ultimo_mantenimiento
        )
        
        # Construir descripción
        descripcion = self._generar_descripcion_falla(resultado)
        
        # Determinar nivel de confianza
        nivel_confianza = self._determinar_nivel_confianza(resultado["confianza"])
        
        # Crear predicción en BD
        prediccion_data = {
            "moto_id": moto_id,
            "usuario_id": usuario_id,
            "tipo": "falla",
            "descripcion": descripcion,
            "confianza": resultado["confianza"],
            "nivel_confianza": nivel_confianza,
            "probabilidad_falla": resultado["probabilidad_falla"],
            "tiempo_estimado_dias": resultado["tiempo_estimado_dias"],
            "fecha_estimada": resultado["fecha_estimada"],
            "modelo_usado": fault_predictor.model_name,
            "version_modelo": fault_predictor.version,
            "datos_entrada": datos_sensor.model_dump(),
            "resultados": resultado,
            "metricas": {
                "severidad": resultado["severidad"],
                "tipo_falla": resultado["tipo_falla_probable"]
            },
            "estado": "pendiente",
            "notificacion_enviada": False
        }
        
        prediccion = await self.prediccion_repo.create(db, prediccion_data)
        
        logger.info(f"Predicción de falla creada: ID={prediccion.id}, confianza={resultado['confianza']:.2f}")
        
        return prediccion
    
    async def detectar_anomalia(
        self,
        db,
        moto_id: int,
        usuario_id: int,
        datos_sensor: DatosSensor
    ) -> Optional[Prediccion]:
        """
        Detecta anomalías en datos de sensores.
        
        Returns:
            Predicción si se detecta anomalía, None si todo es normal
        """
        # Validar datos
        es_valido, errores = validar_datos_anomalia(
            temperatura=datos_sensor.temperatura or 0,
            vibracion=datos_sensor.vibracion or 0,
            rpm=datos_sensor.rpm or 0,
            velocidad=datos_sensor.velocidad or 0,
            presion_aceite=datos_sensor.presion_aceite or 0,
            nivel_combustible=datos_sensor.nivel_combustible or 0
        )
        
        if not es_valido:
            logger.warning(f"Datos de detección con advertencias: {errores}")
        
        # Detectar anomalía
        resultado = anomaly_detector.detect(
            temperatura=datos_sensor.temperatura or 0,
            vibracion=datos_sensor.vibracion or 0,
            rpm=datos_sensor.rpm or 0,
            velocidad=datos_sensor.velocidad or 0,
            presion_aceite=datos_sensor.presion_aceite or 0,
            nivel_combustible=datos_sensor.nivel_combustible or 0
        )
        
        # Si no hay anomalía, retornar None
        if not resultado["es_anomalia"]:
            logger.info(f"No se detectó anomalía para moto {moto_id}")
            return None
        
        # Construir descripción
        descripcion = self._generar_descripcion_anomalia(resultado)
        
        # Determinar nivel de confianza
        nivel_confianza = self._determinar_nivel_confianza(resultado["confianza"])
        
        # Crear predicción en BD
        prediccion_data = {
            "moto_id": moto_id,
            "usuario_id": usuario_id,
            "tipo": "anomalia",
            "descripcion": descripcion,
            "confianza": resultado["confianza"],
            "nivel_confianza": nivel_confianza,
            "probabilidad_falla": None,
            "tiempo_estimado_dias": None,
            "fecha_estimada": None,
            "modelo_usado": anomaly_detector.model_name,
            "version_modelo": anomaly_detector.version,
            "datos_entrada": datos_sensor.model_dump(),
            "resultados": resultado,
            "metricas": {
                "severidad": resultado["severidad"],
                "tipo_anomalia": resultado["tipo_anomalia"],
                "sensores_anomalos": resultado["sensores_anomalos"]
            },
            "estado": "pendiente",
            "notificacion_enviada": False
        }
        
        prediccion = await self.prediccion_repo.create(db, prediccion_data)
        
        logger.warning(
            f"Anomalía detectada: ID={prediccion.id}, "
            f"tipo={resultado['tipo_anomalia']}, "
            f"confianza={resultado['confianza']:.2f}"
        )
        
        return prediccion
    
    async def validar_prediccion(
        self,
        db,
        prediccion_id: int,
        validada_por: int,
        es_correcta: bool
    ) -> Optional[Prediccion]:
        """Valida si una predicción fue correcta o incorrecta."""
        if es_correcta:
            prediccion = await self.prediccion_repo.marcar_como_confirmada(
                db, prediccion_id, validada_por
            )
        else:
            prediccion = await self.prediccion_repo.marcar_como_falsa(
                db, prediccion_id, validada_por
            )
        
        if prediccion:
            logger.info(
                f"Predicción {prediccion_id} validada como "
                f"{'correcta' if es_correcta else 'incorrecta'}"
            )
        
        return prediccion
    
    async def obtener_estadisticas(
        self,
        db,
        moto_id: Optional[int] = None,
        usuario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas de predicciones."""
        return await self.prediccion_repo.get_estadisticas(
            db,
            moto_id=moto_id,
            usuario_id=usuario_id
        )
    
    def _generar_descripcion_falla(self, resultado: Dict[str, Any]) -> str:
        """Genera descripción legible de predicción de falla."""
        prob = resultado["probabilidad_falla"]
        tipo_falla = resultado["tipo_falla_probable"]
        severidad = resultado["severidad"]
        tiempo = resultado.get("tiempo_estimado_dias")
        
        if prob >= 0.85:
            urgencia = "ALTA PROBABILIDAD"
        elif prob >= 0.7:
            urgencia = "Probabilidad moderada"
        else:
            urgencia = "Probabilidad baja"
        
        desc = f"{urgencia} de falla: {tipo_falla.replace('_', ' ').title()}"
        
        if tiempo:
            desc += f". Tiempo estimado: {tiempo} días"
        
        if severidad == "critica":
            desc += " ⚠️ CRÍTICO - Requiere atención inmediata"
        
        return desc
    
    def _generar_descripcion_anomalia(self, resultado: Dict[str, Any]) -> str:
        """Genera descripción legible de anomalía detectada."""
        tipo_anomalia = resultado["tipo_anomalia"]
        severidad = resultado["severidad"]
        sensores = resultado["sensores_anomalos"]
        
        desc = f"Anomalía {tipo_anomalia} detectada"
        
        if sensores:
            sensores_str = ", ".join(s.replace("_", " ") for s in sensores)
            desc += f" en: {sensores_str}"
        
        if severidad == "critica":
            desc += " ⚠️ CRÍTICO"
        elif severidad == "alta":
            desc += " ⚠️ ALTO"
        
        return desc
    
    def _determinar_nivel_confianza(self, confianza: float) -> str:
        """Determina nivel de confianza categórico."""
        if confianza < 0.5:
            return "muy_bajo"
        elif confianza < 0.7:
            return "bajo"
        elif confianza < 0.85:
            return "medio"
        elif confianza < 0.95:
            return "alto"
        else:
            return "muy_alto"


class EntrenamientoService:
    """Servicio para manejo de entrenamientos de modelos."""
    
    def __init__(self, entrenamiento_repo: EntrenamientoRepository):
        self.entrenamiento_repo = entrenamiento_repo
    
    async def registrar_entrenamiento(
        self,
        db,
        nombre_modelo: str,
        version: str,
        metricas: Dict[str, float],
        configuracion: Dict[str, Any]
    ) -> EntrenamientoModelo:
        """Registra un nuevo entrenamiento de modelo."""
        entrenamiento_data = {
            "nombre_modelo": nombre_modelo,
            "version": version,
            "tipo_modelo": configuracion.get("tipo_modelo", "clasificacion"),
            "accuracy": metricas.get("accuracy"),
            "precision": metricas.get("precision"),
            "recall": metricas.get("recall"),
            "f1_score": metricas.get("f1_score"),
            "mse": metricas.get("mse"),
            "rmse": metricas.get("rmse"),
            "num_muestras_entrenamiento": configuracion.get("num_muestras_train", 0),
            "num_muestras_validacion": configuracion.get("num_muestras_val", 0),
            "num_muestras_test": configuracion.get("num_muestras_test", 0),
            "hiperparametros": configuracion.get("hiperparametros", {}),
            "features_usadas": configuracion.get("features", []),
            "ruta_modelo": configuracion.get("ruta_modelo", ""),
            "fecha_inicio": configuracion.get("fecha_inicio", datetime.utcnow()),
            "fecha_fin": configuracion.get("fecha_fin"),
            "en_produccion": False
        }
        
        entrenamiento = await self.entrenamiento_repo.create(db, entrenamiento_data)
        
        logger.info(
            f"Entrenamiento registrado: {nombre_modelo} v{version}, "
            f"accuracy={metricas.get('accuracy', 'N/A')}"
        )
        
        return entrenamiento
    
    async def obtener_modelo_activo(
        self,
        db,
        nombre_modelo: str
    ) -> Optional[EntrenamientoModelo]:
        """Obtiene el modelo actualmente en producción."""
        return await self.entrenamiento_repo.get_en_produccion(db, nombre_modelo)
