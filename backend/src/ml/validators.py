"""
Validadores para el módulo de ML.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime


class MLValidationError(Exception):
    """Excepción para errores de validación de ML."""
    pass


def validar_datos_sensor(datos: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida que los datos de sensores estén en rangos aceptables.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    # Temperatura
    if "temperatura" in datos:
        temp = datos["temperatura"]
        if not isinstance(temp, (int, float)):
            errores.append("Temperatura debe ser numérica")
        elif temp < -50 or temp > 200:
            errores.append("Temperatura fuera de rango (-50 a 200°C)")
    
    # Vibración
    if "vibracion" in datos:
        vib = datos["vibracion"]
        if not isinstance(vib, (int, float)):
            errores.append("Vibración debe ser numérica")
        elif vib < 0 or vib > 100:
            errores.append("Vibración fuera de rango (0 a 100)")
    
    # RPM
    if "rpm" in datos:
        rpm = datos["rpm"]
        if not isinstance(rpm, int):
            errores.append("RPM debe ser entero")
        elif rpm < 0 or rpm > 15000:
            errores.append("RPM fuera de rango (0 a 15000)")
    
    # Velocidad
    if "velocidad" in datos:
        vel = datos["velocidad"]
        if not isinstance(vel, (int, float)):
            errores.append("Velocidad debe ser numérica")
        elif vel < 0 or vel > 300:
            errores.append("Velocidad fuera de rango (0 a 300 km/h)")
    
    # Presión de aceite
    if "presion_aceite" in datos:
        presion = datos["presion_aceite"]
        if not isinstance(presion, (int, float)):
            errores.append("Presión de aceite debe ser numérica")
        elif presion < 0 or presion > 10:
            errores.append("Presión de aceite fuera de rango (0 a 10 bar)")
    
    # Nivel de combustible
    if "nivel_combustible" in datos:
        combustible = datos["nivel_combustible"]
        if not isinstance(combustible, (int, float)):
            errores.append("Nivel de combustible debe ser numérico")
        elif combustible < 0 or combustible > 100:
            errores.append("Nivel de combustible fuera de rango (0 a 100%)")
    
    return len(errores) == 0, errores


def validar_datos_prediccion(
    temperatura: float,
    vibracion: float,
    rpm: int,
    velocidad: float,
    presion_aceite: float,
    kilometraje: int,
    dias_ultimo_mantenimiento: int
) -> Tuple[bool, List[str]]:
    """
    Valida datos para predicción de falla.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    # Validar rangos
    if temperatura < -20 or temperatura > 150:
        errores.append(f"Temperatura anormal: {temperatura}°C")
    
    if vibracion < 0 or vibracion > 100:
        errores.append(f"Vibración fuera de rango: {vibracion}")
    
    if rpm < 0 or rpm > 15000:
        errores.append(f"RPM fuera de rango: {rpm}")
    
    if velocidad < 0 or velocidad > 300:
        errores.append(f"Velocidad fuera de rango: {velocidad} km/h")
    
    if presion_aceite < 0 or presion_aceite > 10:
        errores.append(f"Presión de aceite fuera de rango: {presion_aceite} bar")
    
    if kilometraje < 0:
        errores.append(f"Kilometraje negativo: {kilometraje}")
    
    if dias_ultimo_mantenimiento < 0:
        errores.append(f"Días desde mantenimiento negativo: {dias_ultimo_mantenimiento}")
    
    # Validar combinaciones lógicas
    if rpm > 0 and velocidad == 0:
        # Motor encendido pero no hay velocidad (puede ser normal en punto muerto)
        pass
    
    if temperatura > 130 and presion_aceite < 2:
        errores.append("Condición crítica: alta temperatura con baja presión de aceite")
    
    return len(errores) == 0, errores


def validar_confianza(confianza: float) -> bool:
    """Valida que el valor de confianza esté entre 0 y 1."""
    return 0.0 <= confianza <= 1.0


def validar_modelo_existe(nombre_modelo: str, modelos_disponibles: List[str]) -> bool:
    """Valida que el modelo exista."""
    return nombre_modelo in modelos_disponibles


def validar_hiperparametros(hiperparametros: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Valida hiperparámetros de entrenamiento.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    # Validar estructura básica
    if not isinstance(hiperparametros, dict):
        errores.append("Hiperparámetros deben ser un diccionario")
        return False, errores
    
    # Validar campos comunes
    if "learning_rate" in hiperparametros:
        lr = hiperparametros["learning_rate"]
        if not isinstance(lr, (int, float)) or lr <= 0 or lr > 1:
            errores.append("learning_rate debe estar entre 0 y 1")
    
    if "epochs" in hiperparametros:
        epochs = hiperparametros["epochs"]
        if not isinstance(epochs, int) or epochs <= 0 or epochs > 1000:
            errores.append("epochs debe ser entero entre 1 y 1000")
    
    if "batch_size" in hiperparametros:
        batch = hiperparametros["batch_size"]
        if not isinstance(batch, int) or batch <= 0 or batch > 1024:
            errores.append("batch_size debe ser entero entre 1 y 1024")
    
    return len(errores) == 0, errores


def validar_features(features: List[str]) -> Tuple[bool, List[str]]:
    """
    Valida que las features sean válidas.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    features_validos = [
        "temperatura",
        "vibracion",
        "rpm",
        "velocidad",
        "presion_aceite",
        "nivel_combustible",
        "kilometraje",
        "dias_ultimo_mantenimiento",
        "edad_moto_dias"
    ]
    
    for feature in features:
        if feature not in features_validos:
            errores.append(f"Feature no válido: {feature}")
    
    if len(features) == 0:
        errores.append("Debe especificar al menos un feature")
    
    return len(errores) == 0, errores


def validar_metricas(metricas: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Valida métricas de un modelo.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    metricas_validas = ["accuracy", "precision", "recall", "f1_score", "mse", "rmse"]
    
    for metrica, valor in metricas.items():
        if metrica not in metricas_validas:
            errores.append(f"Métrica no reconocida: {metrica}")
            continue
        
        if not isinstance(valor, (int, float)):
            errores.append(f"Métrica {metrica} debe ser numérica")
            continue
        
        # Métricas de clasificación deben estar entre 0 y 1
        if metrica in ["accuracy", "precision", "recall", "f1_score"]:
            if valor < 0 or valor > 1:
                errores.append(f"Métrica {metrica} debe estar entre 0 y 1")
        
        # Métricas de regresión no deben ser negativas
        if metrica in ["mse", "rmse"] and valor < 0:
            errores.append(f"Métrica {metrica} no puede ser negativa")
    
    return len(errores) == 0, errores


def validar_datos_anomalia(
    temperatura: float,
    vibracion: float,
    rpm: int,
    velocidad: float,
    presion_aceite: float,
    nivel_combustible: float
) -> Tuple[bool, List[str]]:
    """
    Valida datos para detección de anomalías.
    
    Returns:
        Tuple (es_valido, lista_errores)
    """
    errores = []
    
    # Validaciones básicas de rango
    if temperatura < -50 or temperatura > 200:
        errores.append(f"Temperatura extrema: {temperatura}°C")
    
    if vibracion < 0 or vibracion > 100:
        errores.append(f"Vibración fuera de rango: {vibracion}")
    
    if rpm < 0 or rpm > 15000:
        errores.append(f"RPM fuera de rango: {rpm}")
    
    if velocidad < 0 or velocidad > 300:
        errores.append(f"Velocidad fuera de rango: {velocidad} km/h")
    
    if presion_aceite < 0 or presion_aceite > 10:
        errores.append(f"Presión de aceite fuera de rango: {presion_aceite} bar")
    
    if nivel_combustible < 0 or nivel_combustible > 100:
        errores.append(f"Nivel de combustible fuera de rango: {nivel_combustible}%")
    
    return len(errores) == 0, errores


def es_prediccion_valida(
    confianza: float,
    tipo_prediccion: str,
    umbral_minimo: float = 0.5
) -> bool:
    """
    Determina si una predicción es válida basándose en su confianza.
    
    Args:
        confianza: Nivel de confianza de la predicción
        tipo_prediccion: Tipo de predicción
        umbral_minimo: Umbral mínimo de confianza aceptable
        
    Returns:
        True si la predicción es válida
    """
    # Para predicciones críticas, requerir mayor confianza
    tipos_criticos = ["falla", "anomalia"]
    
    if tipo_prediccion in tipos_criticos:
        return confianza >= max(umbral_minimo, 0.7)
    
    return confianza >= umbral_minimo
