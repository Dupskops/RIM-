"""
Script para generar datasets de entrenamiento para modelos ML.
Genera datos sintéticos de sensores con múltiples escenarios.
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.sensores.simulators import SensorDataSimulator, SensorScenarioSimulator
from src.shared.constants import TipoSensor


def generate_sensor_dataset(
    tipo: TipoSensor,
    output_dir: str = "data/ml_datasets",
    samples_per_scenario: int = 1000
) -> dict:
    """
    Genera un dataset completo para un tipo de sensor.
    
    Args:
        tipo: Tipo de sensor
        output_dir: Directorio de salida
        samples_per_scenario: Muestras por escenario
    
    Returns:
        Diccionario con estadísticas del dataset generado
    """
    print(f"\n{'='*60}")
    print(f"Generando dataset para: {tipo.value}")
    print(f"{'='*60}\n")
    
    all_readings = []
    labels = []
    
    # Escenario 1: Operación normal (70% de los datos)
    print("📊 Generando datos normales...")
    normal_samples = int(samples_per_scenario * 0.7)
    for i in range(normal_samples):
        reading = SensorDataSimulator.simulate_sensor_reading(
            sensor_id=1,
            tipo=tipo,
            scenario="normal"
        )
        all_readings.append(reading)
        labels.append("normal")
    
    # Escenario 2: Falla progresiva (10%)
    print("📊 Generando fallas progresivas...")
    failure_samples = int(samples_per_scenario * 0.1)
    failure_readings = SensorScenarioSimulator.simulate_progressive_failure(
        sensor_id=1,
        tipo=tipo,
        steps=failure_samples
    )
    all_readings.extend(failure_readings)
    labels.extend(["progressive_failure"] * failure_samples)
    
    # Escenario 3: Deriva de calibración (10%)
    print("📊 Generando derivas de calibración...")
    drift_samples = int(samples_per_scenario * 0.1)
    drift_readings = SensorScenarioSimulator.simulate_calibration_drift(
        sensor_id=1,
        tipo=tipo,
        steps=drift_samples
    )
    all_readings.extend(drift_readings)
    labels.extend(["calibration_drift"] * drift_samples)
    
    # Escenario 4: Picos anómalos (5%)
    print("📊 Generando picos anómalos...")
    spike_samples = int(samples_per_scenario * 0.05)
    for _ in range(spike_samples // 20):
        spike_readings = SensorScenarioSimulator.simulate_spike_anomaly(
            sensor_id=1,
            tipo=tipo,
            total_readings=20,
            spike_position=10
        )
        all_readings.extend(spike_readings)
        labels.extend(["normal"] * 9 + ["spike_anomaly"] + ["normal"] * 10)
    
    # Escenario 5: Fallas intermitentes (5%)
    print("📊 Generando fallas intermitentes...")
    intermittent_samples = int(samples_per_scenario * 0.05)
    intermittent_readings = SensorScenarioSimulator.simulate_intermittent_failure(
        sensor_id=1,
        tipo=tipo,
        cycles=intermittent_samples
    )
    all_readings.extend(intermittent_readings)
    for i in range(intermittent_samples):
        labels.append("normal" if i % 2 == 0 else "intermittent_failure")
    
    # Crear DataFrame
    print("\n📊 Creando DataFrame...")
    df = pd.DataFrame({
        "sensor_id": [r["sensor_id"] for r in all_readings],
        "valor": [r["valor"] for r in all_readings],
        "timestamp_lectura": [r["timestamp_lectura"] for r in all_readings],
        "label": labels
    })
    
    # Agregar features de metadata
    print("📊 Extrayendo features de metadata...")
    for idx, reading in enumerate(all_readings):
        metadata = reading.get("metadata_json", {})
        df.loc[idx, "battery_level"] = metadata.get("battery_level", None)
        df.loc[idx, "signal_strength"] = metadata.get("signal_strength", None)
    
    # Calcular estadísticas
    stats = {
        "sensor_type": tipo.value,
        "total_samples": len(df),
        "label_distribution": df["label"].value_counts().to_dict(),
        "valor_stats": {
            "mean": float(df["valor"].mean()),
            "std": float(df["valor"].std()),
            "min": float(df["valor"].min()),
            "max": float(df["valor"].max())
        },
        "generated_at": datetime.now().isoformat()
    }
    
    # Crear directorio de salida
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Guardar CSV
    csv_filename = output_path / f"sensor_{tipo.value}_dataset.csv"
    df.to_csv(csv_filename, index=False)
    print(f"\n✅ CSV guardado: {csv_filename}")
    
    # Guardar JSON con estadísticas
    stats_filename = output_path / f"sensor_{tipo.value}_stats.json"
    with open(stats_filename, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✅ Estadísticas guardadas: {stats_filename}")
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN DEL DATASET")
    print(f"{'='*60}")
    print(f"Total de muestras: {stats['total_samples']}")
    print(f"\nDistribución de etiquetas:")
    for label, count in stats["label_distribution"].items():
        percentage = (count / stats['total_samples']) * 100
        print(f"  - {label}: {count} ({percentage:.1f}%)")
    print(f"\nEstadísticas de valores:")
    print(f"  - Media: {stats['valor_stats']['mean']:.2f}")
    print(f"  - Desv. estándar: {stats['valor_stats']['std']:.2f}")
    print(f"  - Mínimo: {stats['valor_stats']['min']:.2f}")
    print(f"  - Máximo: {stats['valor_stats']['max']:.2f}")
    print(f"{'='*60}\n")
    
    return stats


def generate_all_datasets(
    output_dir: str = "data/ml_datasets",
    samples_per_scenario: int = 1000
):
    """
    Genera datasets para todos los tipos de sensores principales.
    
    Args:
        output_dir: Directorio de salida
        samples_per_scenario: Muestras por escenario
    """
    sensor_types = [
        TipoSensor.TEMPERATURA_MOTOR,
        TipoSensor.TEMPERATURA_ACEITE,
        TipoSensor.PRESION_ACEITE,
        TipoSensor.VOLTAJE_BATERIA,
        TipoSensor.VIBRACIONES,
        TipoSensor.RPM,
        TipoSensor.VELOCIDAD,
        TipoSensor.NIVEL_COMBUSTIBLE
    ]
    
    all_stats = []
    
    for tipo in sensor_types:
        try:
            stats = generate_sensor_dataset(
                tipo=tipo,
                output_dir=output_dir,
                samples_per_scenario=samples_per_scenario
            )
            all_stats.append(stats)
        except Exception as e:
            print(f"❌ Error generando dataset para {tipo.value}: {e}")
    
    # Guardar resumen general
    summary_filename = Path(output_dir) / "dataset_summary.json"
    with open(summary_filename, "w") as f:
        json.dump(all_stats, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Todos los datasets generados exitosamente")
    print(f"✅ Resumen guardado en: {summary_filename}")
    print(f"{'='*60}\n")


def generate_time_series_dataset(
    tipo: TipoSensor,
    days: int = 7,
    output_dir: str = "data/ml_datasets"
) -> dict:
    """
    Genera un dataset de series temporales con patrón diario.
    
    Args:
        tipo: Tipo de sensor
        days: Número de días a simular
        output_dir: Directorio de salida
    
    Returns:
        Diccionario con estadísticas
    """
    print(f"\n{'='*60}")
    print(f"Generando dataset de serie temporal para: {tipo.value}")
    print(f"Duración: {days} días")
    print(f"{'='*60}\n")
    
    all_readings = []
    
    for day in range(days):
        print(f"📊 Día {day + 1}/{days}...")
        
        # Generar patrón diario
        daily_readings = SensorScenarioSimulator.simulate_daily_pattern(
            sensor_id=1,
            tipo=tipo,
            hours=24
        )
        
        # Agregar día como feature
        for reading in daily_readings:
            reading["day"] = day + 1
        
        all_readings.extend(daily_readings)
    
    # Crear DataFrame
    df = pd.DataFrame({
        "sensor_id": [r["sensor_id"] for r in all_readings],
        "day": [r["day"] for r in all_readings],
        "valor": [r["valor"] for r in all_readings],
        "timestamp_lectura": [r["timestamp_lectura"] for r in all_readings]
    })
    
    # Guardar
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    csv_filename = output_path / f"sensor_{tipo.value}_timeseries_{days}days.csv"
    df.to_csv(csv_filename, index=False)
    
    stats = {
        "sensor_type": tipo.value,
        "duration_days": days,
        "total_samples": len(df),
        "samples_per_day": 24,
        "generated_at": datetime.now().isoformat()
    }
    
    print(f"\n✅ Serie temporal guardada: {csv_filename}")
    print(f"✅ Total de muestras: {len(df)}")
    print(f"{'='*60}\n")
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generador de datasets para ML de sensores IoT"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "all", "timeseries"],
        default="all",
        help="Modo de generación"
    )
    parser.add_argument(
        "--sensor",
        type=str,
        default="temperatura_motor",
        help="Tipo de sensor (para modo 'single')"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=1000,
        help="Muestras por escenario"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Días para serie temporal"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/ml_datasets",
        help="Directorio de salida"
    )
    
    args = parser.parse_args()
    
    if args.mode == "single":
        tipo = TipoSensor(args.sensor)
        generate_sensor_dataset(
            tipo=tipo,
            output_dir=args.output,
            samples_per_scenario=args.samples
        )
    elif args.mode == "all":
        generate_all_datasets(
            output_dir=args.output,
            samples_per_scenario=args.samples
        )
    elif args.mode == "timeseries":
        tipo = TipoSensor(args.sensor)
        generate_time_series_dataset(
            tipo=tipo,
            days=args.days,
            output_dir=args.output
        )
