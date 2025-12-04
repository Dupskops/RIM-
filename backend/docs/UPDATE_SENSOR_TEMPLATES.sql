-- ============================================
-- ACTUALIZACIÓN: SENSOR TEMPLATES COMPLETOS
-- Archivo: UPDATE_SENSOR_TEMPLATES.sql
-- Descripción: Reemplaza los 5 sensor templates básicos con 11 templates completos
-- Ejecutar DESPUÉS de SEED_DATA_MVP_V2.2.sql
-- ============================================
-- Primero, eliminar los templates incompletos existentes
DELETE FROM sensor_templates
WHERE modelo = 'KTM 390 Duke 2024';
-- ============================================
-- SECCIÓN: 11 SENSOR TEMPLATES COMPLETOS
-- ============================================
-- Cada template incluye:
--   - sensor_type: Tipo de sensor
--   - component_type: mesh_id_3d del componente
--   - parametro_id: ID del parámetro que mide
--   - default_thresholds: Umbrales por defecto
--   - frequency_ms: Frecuencia de muestreo
-- ============================================
DO $$
DECLARE param_temp_id INTEGER;
param_presion_id INTEGER;
param_voltaje_id INTEGER;
param_rpm_id INTEGER;
param_combustible_id INTEGER;
param_kilometraje_id INTEGER;
param_espesor_id INTEGER;
param_holgura_id INTEGER;
BEGIN -- Obtener IDs de parámetros
SELECT id INTO param_temp_id
FROM parametros
WHERE nombre = 'temperatura';
SELECT id INTO param_presion_id
FROM parametros
WHERE nombre = 'presion';
SELECT id INTO param_voltaje_id
FROM parametros
WHERE nombre = 'voltaje';
SELECT id INTO param_rpm_id
FROM parametros
WHERE nombre = 'rpm';
SELECT id INTO param_combustible_id
FROM parametros
WHERE nombre = 'nivel_combustible';
SELECT id INTO param_kilometraje_id
FROM parametros
WHERE nombre = 'kilometraje';
SELECT id INTO param_espesor_id
FROM parametros
WHERE nombre = 'espesor';
SELECT id INTO param_holgura_id
FROM parametros
WHERE nombre = 'holgura';
-- Template 1: Sensor de Temperatura Motor
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Temperatura Motor',
        jsonb_build_object(
            'sensor_type',
            'temperature',
            'component_type',
            'engine_temp',
            'parametro_id',
            param_temp_id,
            'unit',
            '°C',
            'default_thresholds',
            jsonb_build_object('min', 0, 'max', 115),
            'frequency_ms',
            1000,
            'range',
            jsonb_build_object('min', -40, 'max', 150),
            'accuracy',
            0.5,
            'protocol',
            'CAN-Bus'
        )
    );
-- Template 2: Sensor de Presión Neumático Delantero
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Presión Neumático Delantero',
        jsonb_build_object(
            'sensor_type',
            'pressure',
            'component_type',
            'front_tire',
            'parametro_id',
            param_presion_id,
            'unit',
            'bar',
            'default_thresholds',
            jsonb_build_object('min', 2.0, 'max', 2.9),
            'frequency_ms',
            5000,
            'range',
            jsonb_build_object('min', 0, 'max', 5),
            'accuracy',
            0.1,
            'protocol',
            'Bluetooth'
        )
    );
-- Template 3: Sensor de Presión Neumático Trasero
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Presión Neumático Trasero',
        jsonb_build_object(
            'sensor_type',
            'pressure',
            'component_type',
            'rear_tire',
            'parametro_id',
            param_presion_id,
            'unit',
            'bar',
            'default_thresholds',
            jsonb_build_object('min', 2.3, 'max', 3.2),
            'frequency_ms',
            5000,
            'range',
            jsonb_build_object('min', 0, 'max', 5),
            'accuracy',
            0.1,
            'protocol',
            'Bluetooth'
        )
    );
-- Template 4: Sensor de Voltaje Batería
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Voltaje Batería',
        jsonb_build_object(
            'sensor_type',
            'voltage',
            'component_type',
            'electrical_system',
            'parametro_id',
            param_voltaje_id,
            'unit',
            'V',
            'default_thresholds',
            jsonb_build_object('min', 12.0, 'max', 14.5),
            'frequency_ms',
            2000,
            'range',
            jsonb_build_object('min', 0, 'max', 20),
            'accuracy',
            0.1,
            'protocol',
            'CAN-Bus'
        )
    );
-- Template 5: Sensor de RPM Motor
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de RPM Motor',
        jsonb_build_object(
            'sensor_type',
            'rpm',
            'component_type',
            'engine_rpm',
            'parametro_id',
            param_rpm_id,
            'unit',
            'RPM',
            'default_thresholds',
            jsonb_build_object('min', 900, 'max', 11000),
            'frequency_ms',
            500,
            'range',
            jsonb_build_object('min', 0, 'max', 12000),
            'accuracy',
            10,
            'protocol',
            'CAN-Bus'
        )
    );
-- Template 6: Sensor de Nivel de Combustible
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Nivel de Combustible',
        jsonb_build_object(
            'sensor_type',
            'fuel_level',
            'component_type',
            'fuel_tank',
            'parametro_id',
            param_combustible_id,
            'unit',
            'L',
            'default_thresholds',
            jsonb_build_object('min', 1.0, 'max', 13.4),
            'frequency_ms',
            10000,
            'range',
            jsonb_build_object('min', 0, 'max', 13.4),
            'accuracy',
            0.5,
            'protocol',
            'CAN-Bus'
        )
    );
-- Template 7: Sensor de Kilometraje (Servicio Motor)
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Kilometraje Motor',
        jsonb_build_object(
            'sensor_type',
            'odometer',
            'component_type',
            'engine_service',
            'parametro_id',
            param_kilometraje_id,
            'unit',
            'km',
            'default_thresholds',
            jsonb_build_object('min', 0, 'max', 7500),
            'frequency_ms',
            60000,
            'range',
            jsonb_build_object('min', 0, 'max', 999999),
            'accuracy',
            1,
            'protocol',
            'CAN-Bus'
        )
    );
-- Template 8: Sensor de Espesor Disco Freno Delantero
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Espesor Disco Freno Delantero',
        jsonb_build_object(
            'sensor_type',
            'thickness',
            'component_type',
            'front_brake_disc',
            'parametro_id',
            param_espesor_id,
            'unit',
            'mm',
            'default_thresholds',
            jsonb_build_object('min', 3.5, 'max', 5.0),
            'frequency_ms',
            86400000,
            'range',
            jsonb_build_object('min', 0, 'max', 10),
            'accuracy',
            0.1,
            'protocol',
            'Manual'
        )
    );
-- Template 9: Sensor de Espesor Pastillas Freno Delantero
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Espesor Pastillas Freno Delantero',
        jsonb_build_object(
            'sensor_type',
            'thickness',
            'component_type',
            'front_brake_pads',
            'parametro_id',
            param_espesor_id,
            'unit',
            'mm',
            'default_thresholds',
            jsonb_build_object('min', 1.0, 'max', 5.0),
            'frequency_ms',
            86400000,
            'range',
            jsonb_build_object('min', 0, 'max', 10),
            'accuracy',
            0.1,
            'protocol',
            'Manual'
        )
    );
-- Template 10: Sensor de Holgura Cadena de Transmisión
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Holgura Cadena',
        jsonb_build_object(
            'sensor_type',
            'clearance',
            'component_type',
            'chain',
            'parametro_id',
            param_holgura_id,
            'unit',
            'mm',
            'default_thresholds',
            jsonb_build_object('min', 0, 'max', 40),
            'frequency_ms',
            86400000,
            'range',
            jsonb_build_object('min', 0, 'max', 100),
            'accuracy',
            1,
            'protocol',
            'Manual'
        )
    );
-- Template 11: Sensor de Holgura Gomas Rueda Trasera
INSERT INTO sensor_templates (modelo, name, definition)
VALUES (
        'KTM 390 Duke 2024',
        'Sensor de Holgura Gomas Rueda Trasera',
        jsonb_build_object(
            'sensor_type',
            'clearance',
            'component_type',
            'rear_wheel_rubber',
            'parametro_id',
            param_holgura_id,
            'unit',
            'mm',
            'default_thresholds',
            jsonb_build_object('min', 0, 'max', 12),
            'frequency_ms',
            86400000,
            'range',
            jsonb_build_object('min', 0, 'max', 50),
            'accuracy',
            0.5,
            'protocol',
            'Manual'
        )
    );
RAISE NOTICE '============================================';
RAISE NOTICE 'SENSOR TEMPLATES ACTUALIZADOS EXITOSAMENTE';
RAISE NOTICE '============================================';
RAISE NOTICE 'Templates creados: 11 sensores completos';
RAISE NOTICE 'Cada template incluye:';
RAISE NOTICE '  • component_type (mapeo a componente)';
RAISE NOTICE '  • parametro_id (mapeo a parámetro)';
RAISE NOTICE '  • default_thresholds (umbrales)';
RAISE NOTICE '============================================';
END $$;
-- Verificar que se crearon correctamente
SELECT name,
    definition->>'component_type' as component,
    definition->>'parametro_id' as parametro_id,
    definition->>'sensor_type' as sensor_type
FROM sensor_templates
WHERE modelo = 'KTM 390 Duke 2024'
ORDER BY name;