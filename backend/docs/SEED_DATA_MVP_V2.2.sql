-- ============================================
-- Script SEED: RIM- MVP v2.3
-- Base de Datos: PostgreSQL 14+
-- Fecha: 10 de noviembre de 2025
-- Descripción: Datos iniciales con sistema de límites Freemium
-- ============================================
-- ============================================
-- SECCIÓN 1: USUARIOS ADMINISTRATIVOS
-- ============================================
-- Usuario Admin (contraseña: Admin@2024)
-- Hash bcrypt de "Admin@2024": $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIHc3BdXXW
INSERT INTO
    usuarios (email, password_hash, nombre, apellido, telefono, email_verificado, activo, rol)
VALUES
    ('admin@rim-moto.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIHc3BdXXW', 'Administrador', 'Sistema', '+51999999999', TRUE, TRUE, 'admin') ON CONFLICT (email)
DO NOTHING;

COMMENT ON COLUMN usuarios.password_hash IS 'Hash bcrypt. Admin default: Admin@2024';

-- ============================================
-- SECCIÓN 2: PLANES Y CARACTERÍSTICAS
-- ============================================
-- Plan Free
INSERT INTO
    planes (nombre_plan, precio, periodo_facturacion)
VALUES
    ('free', 0.00, 'unico') ON CONFLICT (nombre_plan)
DO NOTHING;

-- Plan Pro
INSERT INTO
    planes (nombre_plan, precio, periodo_facturacion)
VALUES
    ('pro', 29.99, 'mensual') ON CONFLICT (nombre_plan)
DO NOTHING;

-- Características del Sistema (con límites Freemium v2.3)
INSERT INTO
    caracteristicas (clave_funcion, descripcion, limite_free, limite_pro)
VALUES
    -- ============================================
    -- TIER 1: CARACTERÍSTICAS BÁSICAS (Free + Pro) - ILIMITADAS
    -- ============================================
    ('ALERTS_CRITICAL', 'Alertas de componentes críticos (motor, frenos, batería)', NULL, NULL),
    ('SERVICE_HISTORY', 'Historial de servicios y mantenimientos realizados', NULL, NULL),
    ('BASIC_DIAGNOSTICS', 'Diagnóstico general del estado de componentes', NULL, NULL),
    ('LIVE_LOCATION', 'Geolocalización en tiempo real de la moto', NULL, NULL),
    ('TRIP_HISTORY', 'Historial de viajes y rutas recorridas', NULL, NULL),
    ('PERFORMANCE_STATS', 'Estadísticas básicas de rendimiento y uso', NULL, NULL),
    -- ============================================
    -- TIER 2: CARACTERÍSTICAS CON LÍMITE EN FREE
    -- ============================================
    ('CHATBOT', 'Chat IA para diagnóstico y consultas (5 conversaciones/mes)', 5, NULL),
    ('ML_PREDICTIONS', 'Análisis ML con predicciones de fallas (4 análisis/mes)', 4, NULL),
    ('CUSTOM_ALERTS', 'Alertas personalizadas con umbrales custom (máx 3)', 3, NULL),
    ('EXPORT_REPORTS', 'Exportación de reportes en CSV/Excel/PDF (10/mes)', 10, NULL),
    -- ============================================
    -- TIER 3: CARACTERÍSTICAS PREMIUM (Solo Pro)
    -- ============================================
    ('MULTI_BIKE', 'Gestión de múltiples motos (máx 2 en Free)', 2, NULL),
    ('ADVANCED_ANALYTICS', 'Reportes avanzados y analíticas detalladas', 0, NULL),
    ('PREDICTIVE_MAINTENANCE', 'Predicciones automáticas de mantenimiento', 0, NULL),
    ('RIDING_MODES', 'Modos de conducción (Urban, Sport, Off-road)', 0, NULL),
    ('PRIORITY_SUPPORT', 'Soporte técnico prioritario', 0, NULL) ON CONFLICT (clave_funcion)
DO NOTHING;

-- Asignar características a Plan Free (6 básicas ilimitadas + 4 limitadas + 1 premium limitada)
INSERT INTO
    plan_caracteristicas (plan_id, caracteristica_id)
SELECT
    p.id,
    c.id
FROM
    planes p
    CROSS JOIN caracteristicas c
WHERE
    p.nombre_plan = 'free'
    AND c.clave_funcion IN (
        -- TIER 1: Básicas ilimitadas
        'ALERTS_CRITICAL',
        'SERVICE_HISTORY',
        'BASIC_DIAGNOSTICS',
        'LIVE_LOCATION',
        'TRIP_HISTORY',
        'PERFORMANCE_STATS',
        -- TIER 2: Con límites mensuales
        'CHATBOT',
        'ML_PREDICTIONS',
        'CUSTOM_ALERTS',
        'EXPORT_REPORTS',
        -- TIER 3: Premium limitada
        'MULTI_BIKE'
    ) ON CONFLICT (plan_id, caracteristica_id)
DO NOTHING;

-- Asignar TODAS las características a Plan Pro (15 características: 11 básicas/limitadas + 4 premium exclusivas)
INSERT INTO
    plan_caracteristicas (plan_id, caracteristica_id)
SELECT
    p.id,
    c.id
FROM
    planes p
    CROSS JOIN caracteristicas c
WHERE
    p.nombre_plan = 'pro'
    AND c.clave_funcion IN (
        -- TIER 1: Básicas ilimitadas (heredadas)
        'ALERTS_CRITICAL',
        'SERVICE_HISTORY',
        'BASIC_DIAGNOSTICS',
        'LIVE_LOCATION',
        'TRIP_HISTORY',
        'PERFORMANCE_STATS',
        -- TIER 2: Antes limitadas, ahora ilimitadas en Pro
        'CHATBOT',
        'ML_PREDICTIONS',
        'CUSTOM_ALERTS',
        'EXPORT_REPORTS',
        -- TIER 3: Premium (todas)
        'MULTI_BIKE',
        'ADVANCED_ANALYTICS',
        'PREDICTIVE_MAINTENANCE',
        'RIDING_MODES',
        'PRIORITY_SUPPORT'
    ) ON CONFLICT (plan_id, caracteristica_id)
DO NOTHING;

-- Asignar suscripción Pro al admin
INSERT INTO
    suscripciones (usuario_id, plan_id, fecha_inicio, fecha_fin, estado_suscripcion)
SELECT
    u.id,
    p.id,
    CURRENT_TIMESTAMP,
    NULL,
    'activa'
FROM
    usuarios u
    CROSS JOIN planes p
WHERE
    u.email = 'admin@rim-moto.com'
    AND p.nombre_plan = 'pro' ON CONFLICT (usuario_id)
DO NOTHING;

-- ============================================
-- SECCIÓN 3: MODELO DE MOTO MVP - KTM 390 DUKE 2024
-- ============================================
INSERT INTO
    modelos_moto (nombre, marca, año, cilindrada, tipo_motor, especificaciones_tecnicas, activo)
VALUES
    (
        'KTM 390 Duke 2024',
        'KTM',
        2024,
        '373cc',
        'Monocilíndrico 4 tiempos',
        '{
        "potencia_hp": 44,
        "torque_nm": 37,
        "peso_kg": 149,
        "capacidad_tanque_litros": 13.4,
        "transmision": "6 velocidades",
        "abs": true,
        "control_traccion": true,
        "modos_conduccion": ["Rain", "Street", "Sport"],
        "sistema_frenos": {
            "delantero": "Disco simple 320mm ByBre",
            "trasero": "Disco simple 230mm ByBre"
        },
        "neumaticos": {
            "delantero": "110/70 R17",
            "trasero": "150/60 R17"
        }
    }'::jsonb,
        TRUE
    ) ON CONFLICT (nombre)
DO NOTHING;

-- ============================================
-- SECCIÓN 4: PARÁMETROS MEDIBLES
-- ============================================
INSERT INTO
    parametros (nombre, unidad_medida)
VALUES
    ('temperatura', '°C'),
    ('presion', 'bar'),
    ('voltaje', 'V'),
    ('rpm', 'RPM'),
    ('kilometraje', 'km'),
    ('tiempo', 'meses'),
    ('nivel_combustible', 'L'),
    ('espesor', 'mm'),
    ('holgura', 'mm') ON CONFLICT (nombre)
DO NOTHING;

-- ============================================
-- SECCIÓN 5: COMPONENTES KTM 390 DUKE 2024 (11 componentes)
-- ============================================
-- Obtener el ID del modelo KTM 390 Duke 2024
DO $$
DECLARE
    modelo_id INTEGER;
BEGIN
    SELECT id INTO modelo_id FROM modelos_moto WHERE nombre = 'KTM 390 Duke 2024';
    
    -- Componente 1: Motor (Servicio/Aceite)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Motor (Servicio/Aceite)', 'engine_service', 'Control de intervalos de cambio de aceite y servicio del motor')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 2: Depósito de Combustible
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Depósito de Combustible', 'fuel_tank', 'Nivel de combustible en el tanque (capacidad: 13.4L)')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 3: Neumático Delantero
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Neumático Delantero', 'front_tire', 'Presión del neumático delantero 110/70 R17')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 4: Neumático Trasero
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Neumático Trasero', 'rear_tire', 'Presión del neumático trasero 150/60 R17')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 5: Sistema Eléctrico
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Sistema Eléctrico', 'electrical_system', 'Voltaje de batería y sistema eléctrico')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 6: Motor (Temperatura)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Motor (Temperatura)', 'engine_temp', 'Temperatura operativa del motor')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 7: Motor (RPM Ralentí)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Motor (RPM Ralentí)', 'engine_rpm', 'Revoluciones por minuto en ralentí')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 8: Freno Delantero (Disco)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Freno Delantero (Disco)', 'front_brake_disc', 'Espesor del disco delantero 320mm ByBre')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 9: Freno Delantero (Pastillas)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Freno Delantero (Pastillas)', 'front_brake_pads', 'Espesor de pastillas de freno delanteras')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 10: Cadena de Transmisión
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Cadena de Transmisión', 'chain', 'Holgura de la cadena de transmisión')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
    
    -- Componente 11: Rueda Trasera (Gomas)
    INSERT INTO componentes (modelo_moto_id, nombre, mesh_id_3d, descripcion) VALUES
    (modelo_id, 'Rueda Trasera (Gomas)', 'rear_wheel_rubber', 'Holgura de gomas de rueda trasera')
    ON CONFLICT (modelo_moto_id, nombre) DO NOTHING;
END $$;

-- ============================================
-- SECCIÓN 6: REGLAS DE ESTADO (Umbrales Globales)
-- ============================================
DO $$
DECLARE
    modelo_id INTEGER;
    comp_id INTEGER;
    param_id INTEGER;
BEGIN
    SELECT id INTO modelo_id FROM modelos_moto WHERE nombre = 'KTM 390 Duke 2024';
    
    -- Regla 1: Motor (Servicio/Aceite) - Kilometraje
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'engine_service';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'kilometraje';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MENOR_QUE', 5000, 6000, 7500)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 2: Depósito de Combustible - Nivel
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'fuel_tank';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'nivel_combustible';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MAYOR_QUE', 5.0, 3.0, 1.0)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 3: Neumático Delantero - Presión
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'front_tire';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'presion';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'ENTRE', 2.5, 2.0, 1.5)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 4: Neumático Trasero - Presión
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'rear_tire';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'presion';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'ENTRE', 2.9, 2.3, 1.8)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 5: Sistema Eléctrico - Voltaje
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'electrical_system';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'voltaje';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MAYOR_QUE', 13.5, 12.5, 11.5)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 6: Motor (Temperatura) - Temperatura
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'engine_temp';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'temperatura';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MENOR_QUE', 95, 105, 115)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 7: Motor (RPM Ralentí) - RPM
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'engine_rpm';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'rpm';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'ENTRE', 1500, 1200, 900)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 8: Freno Delantero (Disco) - Espesor
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'front_brake_disc';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'espesor';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MAYOR_QUE', 4.5, 4.0, 3.5)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 9: Freno Delantero (Pastillas) - Espesor
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'front_brake_pads';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'espesor';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MAYOR_QUE', 3.0, 2.0, 1.0)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 10: Cadena de Transmisión - Holgura
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'chain';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'holgura';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MENOR_QUE', 20, 30, 40)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
    
    -- Regla 11: Rueda Trasera (Gomas) - Holgura
    SELECT id INTO comp_id FROM componentes WHERE modelo_moto_id = modelo_id AND mesh_id_3d = 'rear_wheel_rubber';
    SELECT id INTO param_id FROM parametros WHERE nombre = 'holgura';
    INSERT INTO reglas_estado (componente_id, parametro_id, logica, limite_bueno, limite_atencion, limite_critico)
    VALUES (comp_id, param_id, 'MENOR_QUE', 5, 8, 12)
    ON CONFLICT (componente_id, parametro_id) DO NOTHING;
END $$;

-- ============================================
-- SECCIÓN 7: SENSOR TEMPLATES (Plantillas IoT)
-- ============================================
DO $$
DECLARE
    modelo_id INTEGER;
BEGIN
    SELECT id INTO modelo_id FROM modelos_moto WHERE nombre = 'KTM 390 Duke 2024';
    
    -- Template: Sensor de Temperatura Motor
    INSERT INTO sensor_templates (modelo, name, definition) VALUES
    ('KTM 390 Duke 2024', 'Sensor de Temperatura Motor', '{
        "type": "temperature",
        "range": {"min": -40, "max": 150},
        "unit": "°C",
        "accuracy": 0.5,
        "sample_rate_ms": 1000,
        "protocol": "CAN-Bus"
    }'::jsonb);
    
    -- Template: Sensor de Presión Neumáticos
    INSERT INTO sensor_templates (modelo, name, definition) VALUES
    ('KTM 390 Duke 2024', 'Sensor de Presión Neumáticos', '{
        "type": "pressure",
        "range": {"min": 0, "max": 5},
        "unit": "bar",
        "accuracy": 0.1,
        "sample_rate_ms": 5000,
        "protocol": "Bluetooth"
    }'::jsonb);
    
    -- Template: Sensor de Voltaje Batería
    INSERT INTO sensor_templates (modelo, name, definition) VALUES
    ('KTM 390 Duke 2024', 'Sensor de Voltaje Batería', '{
        "type": "voltage",
        "range": {"min": 0, "max": 20},
        "unit": "V",
        "accuracy": 0.1,
        "sample_rate_ms": 2000,
        "protocol": "CAN-Bus"
    }'::jsonb);
    
    -- Template: Sensor de RPM
    INSERT INTO sensor_templates (modelo, name, definition) VALUES
    ('KTM 390 Duke 2024', 'Sensor de RPM', '{
        "type": "rpm",
        "range": {"min": 0, "max": 12000},
        "unit": "RPM",
        "accuracy": 10,
        "sample_rate_ms": 500,
        "protocol": "CAN-Bus"
    }'::jsonb);
    
    -- Template: Sensor de Nivel Combustible
    INSERT INTO sensor_templates (modelo, name, definition) VALUES
    ('KTM 390 Duke 2024', 'Sensor de Nivel Combustible', '{
        "type": "fuel_level",
        "range": {"min": 0, "max": 13.4},
        "unit": "L",
        "accuracy": 0.5,
        "sample_rate_ms": 10000,
        "protocol": "CAN-Bus"
    }'::jsonb);
END $$;

-- ============================================
-- SECCIÓN 8: PREFERENCIAS DE NOTIFICACIONES DEFAULT
-- ============================================
-- Crear preferencia default para el admin
INSERT INTO
    preferencias_notificaciones (usuario_id, canales_habilitados, tipos_habilitados, no_molestar_inicio, no_molestar_fin, configuracion_adicional)
SELECT
    u.id,
    '{"in_app": true, "email": true, "push": false, "sms": false}'::jsonb,
    '{"fallas": true, "mantenimiento": true, "predicciones": true, "viajes": false, "marketing": false}'::jsonb,
    '22:00'::TIME,
    '08:00'::TIME,
    '{"idioma": "es", "zona_horaria": "America/Lima"}'::jsonb
FROM
    usuarios u
WHERE
    u.email = 'admin@rim-moto.com' ON CONFLICT (usuario_id)
DO NOTHING;

-- ============================================
-- SECCIÓN 9: RESUMEN DE DATOS INSERTADOS
-- ============================================
DO $$
DECLARE
    free_features INTEGER;
    pro_features INTEGER;
    limited_features INTEGER;
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE 'SEED COMPLETADO EXITOSAMENTE - MVP v2.3';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Usuarios creados: %', (SELECT COUNT(*) FROM usuarios);
    RAISE NOTICE 'Planes creados: %', (SELECT COUNT(*) FROM planes);
    RAISE NOTICE 'Características creadas: %', (SELECT COUNT(*) FROM caracteristicas);
    RAISE NOTICE 'Modelos de moto: %', (SELECT COUNT(*) FROM modelos_moto);
    RAISE NOTICE 'Componentes KTM 390 Duke 2024: %', (SELECT COUNT(*) FROM componentes);
    RAISE NOTICE 'Parámetros definidos: %', (SELECT COUNT(*) FROM parametros);
    RAISE NOTICE 'Reglas de estado: %', (SELECT COUNT(*) FROM reglas_estado);
    RAISE NOTICE 'Sensor templates: %', (SELECT COUNT(*) FROM sensor_templates);
    RAISE NOTICE '--------------------------------------------';
    
    -- Contar características por plan
    SELECT COUNT(*) INTO free_features 
    FROM plan_caracteristicas pc
    JOIN planes p ON pc.plan_id = p.id
    WHERE p.nombre_plan = 'free';
    
    SELECT COUNT(*) INTO pro_features 
    FROM plan_caracteristicas pc
    JOIN planes p ON pc.plan_id = p.id
    WHERE p.nombre_plan = 'pro';
    
    -- Contar características con límite en Free
    SELECT COUNT(*) INTO limited_features
    FROM caracteristicas
    WHERE limite_free IS NOT NULL AND limite_free > 0;
    
    RAISE NOTICE 'DISTRIBUCIÓN DE CARACTERÍSTICAS (FREEMIUM v2.3):';
    RAISE NOTICE 'Plan Free: % características disponibles', free_features;
    RAISE NOTICE '';
    RAISE NOTICE '  📦 TIER 1: Básicas ilimitadas (6)';
    RAISE NOTICE '    • Alertas críticas';
    RAISE NOTICE '    • Historial servicios';
    RAISE NOTICE '    • Diagnósticos básicos';
    RAISE NOTICE '    • Localización en vivo';
    RAISE NOTICE '    • Historial de viajes';
    RAISE NOTICE '    • Estadísticas rendimiento';
    RAISE NOTICE '';
    RAISE NOTICE '  📊 TIER 2: Con límites mensuales (4)';
    RAISE NOTICE '    • Chatbot IA: 5 conversaciones/mes';
    RAISE NOTICE '    • Análisis ML: 4 análisis/mes';
    RAISE NOTICE '    • Alertas personalizadas: 3 máx activas';
    RAISE NOTICE '    • Exportar reportes: 10/mes';
    RAISE NOTICE '';
    RAISE NOTICE '  ⭐ TIER 3: Premium limitada (1)';
    RAISE NOTICE '    • Múltiples motos: 2 máx';
    RAISE NOTICE '';
    RAISE NOTICE 'Plan Pro: % características (TODAS ilimitadas)', pro_features;
    RAISE NOTICE '';
    RAISE NOTICE '  ✅ TIER 1+2: Todas ilimitadas (10)';
    RAISE NOTICE '  ✨ TIER 3: Premium exclusivas (5)';
    RAISE NOTICE '    • Múltiples motos: ilimitadas';
    RAISE NOTICE '    • Analíticas avanzadas';
    RAISE NOTICE '    • Mantenimiento predictivo';
    RAISE NOTICE '    • Modos de conducción';
    RAISE NOTICE '    • Soporte prioritario';
    RAISE NOTICE '--------------------------------------------';
    RAISE NOTICE 'CREDENCIALES DE ACCESO:';
    RAISE NOTICE 'Email: admin@rim-moto.com';
    RAISE NOTICE 'Password: Admin@2024';
    RAISE NOTICE 'Plan: Pro (acceso completo sin límites)';
    RAISE NOTICE '============================================';
END $$;

-- ============================================
-- FIN DEL SCRIPT SEED
-- ============================================