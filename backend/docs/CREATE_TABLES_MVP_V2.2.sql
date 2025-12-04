-- ============================================
-- Script DDL: RIM- MVP v2.3
-- Base de Datos: PostgreSQL 14+
-- Fecha: 10 de noviembre de 2025
-- Descripción: Creación de 28 tablas con ENUMs, constraints y límites Freemium
-- ============================================

-- ============================================
-- SECCIÓN 1: EXTENSIONES Y CONFIGURACIÓN
-- ============================================

-- Habilitar extensión UUID (para sensores IoT)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- SECCIÓN 2: TIPOS ENUMERADOS (ENUMs)
-- ============================================

-- Auth & Usuarios
CREATE TYPE rol_usuario AS ENUM ('user', 'admin');

-- Suscripciones
CREATE TYPE periodo_facturacion_enum AS ENUM ('mensual', 'anual', 'unico');
CREATE TYPE estado_suscripcion_enum AS ENUM ('activa', 'cancelada', 'pendiente_pago');

-- Componentes y Estado
CREATE TYPE estado_componente AS ENUM ('EXCELENTE', 'BUENO', 'ATENCION', 'CRITICO', 'FRIO');
CREATE TYPE logica_regla AS ENUM ('MAYOR_QUE', 'MENOR_QUE', 'ENTRE');

-- Sensores
CREATE TYPE sensor_state_enum AS ENUM ('ok', 'degraded', 'faulty', 'offline', 'unknown');

-- Fallas
CREATE TYPE severidad_falla AS ENUM ('baja', 'media', 'alta', 'critica');
CREATE TYPE estado_falla AS ENUM ('detectada', 'en_reparacion', 'resuelta');
CREATE TYPE origen_deteccion AS ENUM ('sensor', 'ml', 'manual');

-- Mantenimiento
CREATE TYPE tipo_mantenimiento AS ENUM (
    'cambio_aceite',
    'cambio_filtro_aire',
    'cambio_llantas',
    'revision_frenos',
    'ajuste_cadena',
    'revision_general',
    'cambio_bateria',
    'cambio_bujias'
);
CREATE TYPE estado_mantenimiento AS ENUM ('pendiente', 'en_proceso', 'completado', 'cancelado');

-- Notificaciones
CREATE TYPE tipo_notificacion AS ENUM ('info', 'warning', 'alert', 'success', 'error');
CREATE TYPE canal_notificacion AS ENUM ('in_app', 'email', 'push', 'sms');
CREATE TYPE estado_notificacion AS ENUM ('pendiente', 'enviada', 'leida', 'fallida');
CREATE TYPE referencia_tipo_enum AS ENUM ('falla', 'mantenimiento', 'sensor', 'prediccion');

-- Chatbot
CREATE TYPE role_mensaje AS ENUM ('user', 'assistant');
CREATE TYPE tipo_prompt AS ENUM ('diagnostic', 'maintenance', 'explanation', 'general');

-- Machine Learning
CREATE TYPE tipo_prediccion AS ENUM ('falla', 'anomalia', 'mantenimiento', 'desgaste');
CREATE TYPE nivel_confianza AS ENUM ('muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto');
CREATE TYPE estado_prediccion AS ENUM ('pendiente', 'confirmada', 'falsa', 'expirada');
CREATE TYPE tipo_modelo_ml AS ENUM ('clasificacion', 'regresion', 'clustering');

-- Alertas Personalizadas
CREATE TYPE operador_alerta AS ENUM ('MAYOR_QUE', 'MENOR_QUE', 'IGUAL_A');
CREATE TYPE nivel_severidad_alerta AS ENUM ('info', 'warning', 'critical');

-- ============================================
-- SECCIÓN 3: TABLAS - MÓDULO AUTH & USUARIOS
-- ============================================

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    email_verificado BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    rol rol_usuario DEFAULT 'user',
    ultimo_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_activo ON usuarios(activo) WHERE activo = TRUE;
CREATE INDEX idx_usuarios_deleted_at ON usuarios(deleted_at) WHERE deleted_at IS NULL;

COMMENT ON TABLE usuarios IS 'Tabla de usuarios del sistema con autenticación';
COMMENT ON COLUMN usuarios.email IS 'Email único del usuario, usado para login';
COMMENT ON COLUMN usuarios.password_hash IS 'Hash bcrypt de la contraseña';

-- Refresh Tokens (JWT)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revocado BOOLEAN DEFAULT FALSE,
    revocado_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_expires_at_future CHECK (expires_at > created_at)
);

CREATE INDEX idx_refresh_tokens_usuario ON refresh_tokens(usuario_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token) WHERE revocado = FALSE;
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    usado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_reset_expires_future CHECK (expires_at > created_at)
);

CREATE INDEX idx_password_reset_usuario ON password_reset_tokens(usuario_id);
CREATE INDEX idx_password_reset_token ON password_reset_tokens(token) WHERE usado = FALSE;

-- Email Verification Tokens
CREATE TABLE email_verification_tokens (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    usado_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_verify_expires_future CHECK (expires_at > created_at)
);

CREATE INDEX idx_email_verification_usuario ON email_verification_tokens(usuario_id);
CREATE INDEX idx_email_verification_token ON email_verification_tokens(token) WHERE usado = FALSE;

-- ============================================
-- SECCIÓN 4: TABLAS - MÓDULO SUSCRIPCIONES
-- ============================================

CREATE TABLE planes (
    id SERIAL PRIMARY KEY,
    nombre_plan VARCHAR(50) NOT NULL UNIQUE,
    precio DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    periodo_facturacion periodo_facturacion_enum NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_precio_no_negativo CHECK (precio >= 0),
    CONSTRAINT chk_nombre_plan_valido CHECK (nombre_plan IN ('free', 'pro'))
);

CREATE INDEX idx_planes_nombre ON planes(nombre_plan);

COMMENT ON TABLE planes IS 'Planes de suscripción: free (gratis) y pro (pago)';
COMMENT ON COLUMN planes.precio IS '0.00 para free, >0 para pro';

-- Características (Features)
CREATE TABLE caracteristicas (
    id SERIAL PRIMARY KEY,
    clave_funcion VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    limite_free INTEGER NULL,
    limite_pro INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_caracteristicas_clave ON caracteristicas(clave_funcion);

COMMENT ON TABLE caracteristicas IS 'Características disponibles con límites mensuales (v2.3)';
COMMENT ON COLUMN caracteristicas.limite_free IS 'Límite mensual para usuarios Free. NULL = ilimitado, 0 = bloqueado';
COMMENT ON COLUMN caracteristicas.limite_pro IS 'Límite mensual para usuarios Pro. NULL = ilimitado';

-- Tabla de unión Plan-Características
CREATE TABLE plan_caracteristicas (
    plan_id INTEGER NOT NULL REFERENCES planes(id) ON DELETE CASCADE,
    caracteristica_id INTEGER NOT NULL REFERENCES caracteristicas(id) ON DELETE CASCADE,
    PRIMARY KEY (plan_id, caracteristica_id)
);

CREATE INDEX idx_plan_caracteristicas_plan ON plan_caracteristicas(plan_id);
CREATE INDEX idx_plan_caracteristicas_feature ON plan_caracteristicas(caracteristica_id);

-- Suscripciones de usuarios
CREATE TABLE suscripciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES planes(id),
    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    estado_suscripcion estado_suscripcion_enum DEFAULT 'activa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_fecha_fin_posterior CHECK (fecha_fin IS NULL OR fecha_fin > fecha_inicio)
);

CREATE INDEX idx_suscripciones_usuario ON suscripciones(usuario_id);
CREATE INDEX idx_suscripciones_plan ON suscripciones(plan_id);
CREATE INDEX idx_suscripciones_estado ON suscripciones(estado_suscripcion);

COMMENT ON TABLE suscripciones IS 'Un usuario tiene una suscripción activa. fecha_fin NULL = free o vitalicio';

-- Uso de Características (control de límites mensuales)
CREATE TABLE uso_caracteristicas (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    caracteristica_id INTEGER NOT NULL REFERENCES caracteristicas(id) ON DELETE CASCADE,
    periodo_mes DATE NOT NULL,
    usos_realizados INTEGER NOT NULL DEFAULT 0,
    limite_mensual INTEGER NOT NULL,
    ultimo_uso_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    CONSTRAINT uk_uso_usuario_feature_periodo UNIQUE(usuario_id, caracteristica_id, periodo_mes),
    CONSTRAINT chk_usos_no_negativos CHECK (usos_realizados >= 0),
    CONSTRAINT chk_limite_positivo CHECK (limite_mensual > 0)
);

CREATE INDEX idx_uso_caracteristicas_usuario_periodo 
    ON uso_caracteristicas(usuario_id, periodo_mes) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_uso_caracteristicas_caracteristica 
    ON uso_caracteristicas(caracteristica_id) 
    WHERE deleted_at IS NULL;
CREATE INDEX idx_uso_caracteristicas_lookup 
    ON uso_caracteristicas(usuario_id, caracteristica_id, periodo_mes) 
    WHERE deleted_at IS NULL;

COMMENT ON TABLE uso_caracteristicas IS 'Control de uso mensual de características con límites (v2.3)';
COMMENT ON COLUMN uso_caracteristicas.periodo_mes IS 'Primer día del mes (ej: 2025-11-01 para noviembre)';
COMMENT ON COLUMN uso_caracteristicas.usos_realizados IS 'Contador de usos en el periodo actual';
COMMENT ON COLUMN uso_caracteristicas.limite_mensual IS 'Límite máximo de usos para el periodo';

-- ============================================
-- SECCIÓN 5: TABLAS - MÓDULO MOTOS Y COMPONENTES
-- ============================================

-- Modelos de Moto (Catálogo)
CREATE TABLE modelos_moto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    marca VARCHAR(50) NOT NULL,
    año INTEGER NOT NULL,
    cilindrada VARCHAR(20),
    tipo_motor VARCHAR(50),
    especificaciones_tecnicas JSONB,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_año_valido CHECK (año BETWEEN 1900 AND 2100)
);

CREATE INDEX idx_modelos_moto_nombre ON modelos_moto(nombre);
CREATE INDEX idx_modelos_moto_marca ON modelos_moto(marca);
CREATE INDEX idx_modelos_moto_activo ON modelos_moto(activo) WHERE activo = TRUE;

COMMENT ON TABLE modelos_moto IS 'Catálogo de modelos de motos. MVP: KTM 390 Duke 2024';
COMMENT ON COLUMN modelos_moto.año IS 'Año del modelo (ej: 2024 para KTM 390 Duke 2024)';

-- Motos de usuarios
CREATE TABLE motos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    modelo_moto_id INTEGER NOT NULL REFERENCES modelos_moto(id),
    vin VARCHAR(17) NOT NULL UNIQUE,
    placa VARCHAR(20) NOT NULL UNIQUE,
    color VARCHAR(50),
    kilometraje_actual DECIMAL(10, 2) DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_vin_length CHECK (LENGTH(vin) = 17),
    CONSTRAINT chk_kilometraje_no_negativo CHECK (kilometraje_actual >= 0)
);

CREATE INDEX idx_motos_usuario ON motos(usuario_id);
CREATE INDEX idx_motos_modelo ON motos(modelo_moto_id);
CREATE INDEX idx_motos_vin ON motos(vin);
CREATE INDEX idx_motos_placa ON motos(placa);

COMMENT ON TABLE motos IS 'Motos registradas por usuarios';
COMMENT ON COLUMN motos.vin IS 'VIN único de 17 caracteres';

-- Componentes (por modelo)
CREATE TABLE componentes (
    id SERIAL PRIMARY KEY,
    modelo_moto_id INTEGER NOT NULL REFERENCES modelos_moto(id),
    nombre VARCHAR(100) NOT NULL,
    mesh_id_3d VARCHAR(100) UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_componente_modelo_nombre UNIQUE (modelo_moto_id, nombre)
);

CREATE INDEX idx_componentes_modelo ON componentes(modelo_moto_id);
CREATE INDEX idx_componentes_mesh ON componentes(mesh_id_3d);

COMMENT ON TABLE componentes IS 'Componentes medibles por modelo. KTM 390 Duke 2024: 11 componentes';
COMMENT ON COLUMN componentes.mesh_id_3d IS 'ID para renderizado 3D en frontend';

-- Parámetros (métricas)
CREATE TABLE parametros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    unidad_medida VARCHAR(20) NOT NULL
);

CREATE INDEX idx_parametros_nombre ON parametros(nombre);

COMMENT ON TABLE parametros IS 'Parámetros medibles: temperatura, presion, voltaje, etc.';
COMMENT ON COLUMN parametros.unidad_medida IS 'Unidad: °C, bar, V, mm, L, RPM';

-- Reglas de Estado (umbrales globales)
CREATE TABLE reglas_estado (
    id SERIAL PRIMARY KEY,
    componente_id INTEGER NOT NULL REFERENCES componentes(id) ON DELETE CASCADE,
    parametro_id INTEGER NOT NULL REFERENCES parametros(id) ON DELETE CASCADE,
    logica logica_regla NOT NULL,
    limite_bueno DECIMAL(10, 2),
    limite_atencion DECIMAL(10, 2),
    limite_critico DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_regla_componente_parametro UNIQUE (componente_id, parametro_id)
);

CREATE INDEX idx_reglas_componente ON reglas_estado(componente_id);
CREATE INDEX idx_reglas_parametro ON reglas_estado(parametro_id);

COMMENT ON TABLE reglas_estado IS 'Umbrales globales por componente-parámetro';

-- Estado Actual (estado en tiempo real por moto-componente)
CREATE TABLE estado_actual (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    componente_id INTEGER NOT NULL REFERENCES componentes(id) ON DELETE CASCADE,
    ultimo_valor DECIMAL(10, 2),
    estado estado_componente NOT NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_estado_moto_componente UNIQUE (moto_id, componente_id)
);

CREATE INDEX idx_estado_actual_moto ON estado_actual(moto_id);
CREATE INDEX idx_estado_actual_componente ON estado_actual(componente_id);
CREATE INDEX idx_estado_actual_estado ON estado_actual(estado);

COMMENT ON TABLE estado_actual IS 'Estado en tiempo real de cada componente por moto';
COMMENT ON COLUMN estado_actual.estado IS 'EXCELENTE, BUENO, ATENCION, CRITICO, FRIO';

-- Alertas Personalizadas
CREATE TABLE alertas_personalizadas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    componente_id INTEGER NOT NULL REFERENCES componentes(id) ON DELETE CASCADE,
    parametro_id INTEGER NOT NULL REFERENCES parametros(id) ON DELETE CASCADE,
    nombre VARCHAR(200) NOT NULL,
    umbral_personalizado DECIMAL(10, 2) NOT NULL,
    operador operador_alerta NOT NULL,
    nivel_severidad nivel_severidad_alerta DEFAULT 'warning',
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_alertas_usuario ON alertas_personalizadas(usuario_id);
CREATE INDEX idx_alertas_moto ON alertas_personalizadas(moto_id);
CREATE INDEX idx_alertas_componente ON alertas_personalizadas(componente_id);
CREATE INDEX idx_alertas_activa ON alertas_personalizadas(activa) WHERE activa = TRUE;

COMMENT ON TABLE alertas_personalizadas IS 'Umbrales custom por usuario (ej: alertar si temp > 95°C)';

-- ============================================
-- SECCIÓN 6: TABLAS - MÓDULO SENSORES IOT
-- ============================================

-- Plantillas de Sensores
CREATE TABLE sensor_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    modelo VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    definition JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensor_templates_modelo ON sensor_templates(modelo);

COMMENT ON TABLE sensor_templates IS 'Plantillas de sensores IoT por modelo de moto';

-- Sensores (instancias)
CREATE TABLE sensores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    template_id UUID REFERENCES sensor_templates(id),
    parametro_id INTEGER NOT NULL REFERENCES parametros(id),
    componente_id INTEGER NOT NULL REFERENCES componentes(id),
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    config JSONB,
    sensor_state sensor_state_enum DEFAULT 'unknown',
    last_value JSONB,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensores_moto ON sensores(moto_id);
CREATE INDEX idx_sensores_componente ON sensores(componente_id);
CREATE INDEX idx_sensores_parametro ON sensores(parametro_id);
CREATE INDEX idx_sensores_state ON sensores(sensor_state);

COMMENT ON TABLE sensores IS 'Instancias de sensores IoT por moto';
COMMENT ON COLUMN sensores.sensor_state IS 'ok, degraded, faulty, offline, unknown';

-- Lecturas (telemetría)
CREATE TABLE lecturas (
    id BIGSERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    sensor_id UUID NOT NULL REFERENCES sensores(id) ON DELETE CASCADE,
    componente_id INTEGER NOT NULL REFERENCES componentes(id),
    parametro_id INTEGER NOT NULL REFERENCES parametros(id),
    ts TIMESTAMP NOT NULL,
    valor JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lecturas_moto ON lecturas(moto_id);
CREATE INDEX idx_lecturas_sensor ON lecturas(sensor_id);
CREATE INDEX idx_lecturas_componente ON lecturas(componente_id);
CREATE INDEX idx_lecturas_ts ON lecturas(ts DESC);
CREATE INDEX idx_lecturas_moto_ts ON lecturas(moto_id, ts DESC);
CREATE INDEX idx_lecturas_sensor_ts ON lecturas(sensor_id, ts DESC);

COMMENT ON TABLE lecturas IS 'Telemetría en tiempo real. BigInt para millones de registros';
COMMENT ON COLUMN lecturas.ts IS 'Timestamp de la lectura del sensor';
COMMENT ON COLUMN lecturas.valor IS 'Valor y metadatos de la lectura';

-- ============================================
-- SECCIÓN 7: TABLAS - MÓDULO FALLAS Y MANTENIMIENTO
-- ============================================

-- Fallas
CREATE TABLE fallas (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    sensor_id UUID REFERENCES sensores(id) ON DELETE SET NULL,
    componente_id INTEGER NOT NULL REFERENCES componentes(id),
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    tipo VARCHAR(100) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    severidad severidad_falla NOT NULL,
    estado estado_falla DEFAULT 'detectada',
    origen_deteccion origen_deteccion NOT NULL,
    valor_actual DECIMAL(10, 2),
    valor_esperado DECIMAL(10, 2),
    requiere_atencion_inmediata BOOLEAN DEFAULT FALSE,
    puede_conducir BOOLEAN DEFAULT TRUE,
    solucion_sugerida TEXT,
    fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_codigo_falla_format CHECK (codigo ~ '^FL-\d{8}-\d{3}$'),
    CONSTRAINT chk_fecha_resolucion_posterior CHECK (fecha_resolucion IS NULL OR fecha_resolucion >= fecha_deteccion)
);

CREATE INDEX idx_fallas_moto ON fallas(moto_id);
CREATE INDEX idx_fallas_componente ON fallas(componente_id);
CREATE INDEX idx_fallas_sensor ON fallas(sensor_id);
CREATE INDEX idx_fallas_codigo ON fallas(codigo);
CREATE INDEX idx_fallas_estado ON fallas(estado);
CREATE INDEX idx_fallas_severidad ON fallas(severidad);
CREATE INDEX idx_fallas_fecha_deteccion ON fallas(fecha_deteccion DESC);

COMMENT ON TABLE fallas IS 'Fallas detectadas por sensores, ML o reportadas manualmente';
COMMENT ON COLUMN fallas.codigo IS 'Formato: FL-YYYYMMDD-NNN (ej: FL-20250110-001)';

-- Mantenimientos
CREATE TABLE mantenimientos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    falla_relacionada_id INTEGER REFERENCES fallas(id) ON DELETE SET NULL,
    tipo tipo_mantenimiento NOT NULL,
    estado estado_mantenimiento DEFAULT 'pendiente',
    kilometraje_actual INTEGER,
    kilometraje_siguiente INTEGER,
    fecha_programada DATE,
    fecha_completado TIMESTAMP,
    descripcion TEXT,
    notas_tecnico TEXT,
    costo_estimado DECIMAL(10, 2),
    costo_real DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_codigo_mantenimiento_format CHECK (codigo ~ '^MNT-\d{8}-\d{3}$'),
    CONSTRAINT chk_kilometraje_valido CHECK (kilometraje_actual IS NULL OR kilometraje_actual >= 0),
    CONSTRAINT chk_kilometraje_siguiente_mayor CHECK (kilometraje_siguiente IS NULL OR kilometraje_siguiente > kilometraje_actual),
    CONSTRAINT chk_costos_no_negativos CHECK (
        (costo_estimado IS NULL OR costo_estimado >= 0) AND
        (costo_real IS NULL OR costo_real >= 0)
    )
);

CREATE INDEX idx_mantenimientos_moto ON mantenimientos(moto_id);
CREATE INDEX idx_mantenimientos_falla ON mantenimientos(falla_relacionada_id);
CREATE INDEX idx_mantenimientos_codigo ON mantenimientos(codigo);
CREATE INDEX idx_mantenimientos_estado ON mantenimientos(estado);
CREATE INDEX idx_mantenimientos_tipo ON mantenimientos(tipo);
CREATE INDEX idx_mantenimientos_fecha_programada ON mantenimientos(fecha_programada);

COMMENT ON TABLE mantenimientos IS 'Servicios y reparaciones (preventivo, correctivo, inspección)';
COMMENT ON COLUMN mantenimientos.codigo IS 'Formato: MNT-YYYYMMDD-NNN (ej: MNT-20250110-001)';

-- ============================================
-- SECCIÓN 8: TABLAS - MÓDULO VIAJES
-- ============================================

CREATE TABLE viajes (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    timestamp_inicio TIMESTAMP NOT NULL,
    timestamp_fin TIMESTAMP,
    distancia_km DECIMAL(10, 2),
    velocidad_media_kmh DECIMAL(5, 2),
    kilometraje_inicio DECIMAL(10, 2),
    kilometraje_fin DECIMAL(10, 2),
    ruta_gps JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_timestamp_fin_posterior CHECK (timestamp_fin IS NULL OR timestamp_fin > timestamp_inicio),
    CONSTRAINT chk_distancia_no_negativa CHECK (distancia_km IS NULL OR distancia_km >= 0),
    CONSTRAINT chk_velocidad_valida CHECK (velocidad_media_kmh IS NULL OR velocidad_media_kmh >= 0),
    CONSTRAINT chk_kilometraje_viaje_valido CHECK (
        kilometraje_fin IS NULL OR kilometraje_inicio IS NULL OR kilometraje_fin >= kilometraje_inicio
    )
);

CREATE INDEX idx_viajes_moto ON viajes(moto_id);
CREATE INDEX idx_viajes_usuario ON viajes(usuario_id);
CREATE INDEX idx_viajes_timestamp_inicio ON viajes(timestamp_inicio DESC);

COMMENT ON TABLE viajes IS 'Tracking de viajes con GPS opcional';
COMMENT ON COLUMN viajes.ruta_gps IS 'Array de puntos GPS: [{lat, lon, ts}, ...]';

-- ============================================
-- SECCIÓN 9: TABLAS - MÓDULO NOTIFICACIONES
-- ============================================

-- Notificaciones
CREATE TABLE notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo tipo_notificacion NOT NULL,
    canal canal_notificacion NOT NULL,
    estado estado_notificacion DEFAULT 'pendiente',
    referencia_tipo referencia_tipo_enum,
    referencia_id INTEGER,
    leida BOOLEAN DEFAULT FALSE,
    leida_en TIMESTAMP,
    intentos_envio INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_notificaciones_usuario ON notificaciones(usuario_id);
CREATE INDEX idx_notificaciones_estado ON notificaciones(estado);
CREATE INDEX idx_notificaciones_leida ON notificaciones(leida);
CREATE INDEX idx_notificaciones_tipo ON notificaciones(tipo);
CREATE INDEX idx_notificaciones_created ON notificaciones(created_at DESC);

COMMENT ON TABLE notificaciones IS 'Notificaciones multi-canal (in-app, email, push, SMS)';

-- Preferencias de Notificaciones
CREATE TABLE preferencias_notificaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    canales_habilitados JSONB DEFAULT '{"in_app": true, "email": false, "push": false, "sms": false}'::jsonb,
    tipos_habilitados JSONB DEFAULT '{"fallas": true, "mantenimiento": true, "predicciones": true}'::jsonb,
    no_molestar_inicio TIME,
    no_molestar_fin TIME,
    configuracion_adicional JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_preferencias_usuario ON preferencias_notificaciones(usuario_id);

COMMENT ON TABLE preferencias_notificaciones IS 'Preferencias de notificaciones por usuario';
COMMENT ON COLUMN preferencias_notificaciones.no_molestar_inicio IS 'Hora inicio período "No molestar" (ej: 22:00)';

-- ============================================
-- SECCIÓN 10: TABLAS - MÓDULO CHATBOT IA
-- ============================================

-- Conversaciones
CREATE TABLE conversaciones (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL UNIQUE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    titulo VARCHAR(200),
    activa BOOLEAN DEFAULT TRUE,
    total_mensajes INTEGER DEFAULT 0,
    ultima_actividad TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_total_mensajes_no_negativo CHECK (total_mensajes >= 0)
);

CREATE INDEX idx_conversaciones_usuario ON conversaciones(usuario_id);
CREATE INDEX idx_conversaciones_moto ON conversaciones(moto_id);
CREATE INDEX idx_conversaciones_conversation_id ON conversaciones(conversation_id);
CREATE INDEX idx_conversaciones_activa ON conversaciones(activa) WHERE activa = TRUE;
CREATE INDEX idx_conversaciones_ultima_actividad ON conversaciones(ultima_actividad DESC);

COMMENT ON TABLE conversaciones IS 'Sesiones de chat con IA (Llama3 local)';

-- Mensajes
CREATE TABLE mensajes (
    id SERIAL PRIMARY KEY,
    conversacion_id INTEGER NOT NULL REFERENCES conversaciones(id) ON DELETE CASCADE,
    role role_mensaje NOT NULL,
    contenido TEXT NOT NULL,
    tipo_prompt tipo_prompt DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mensajes_conversacion ON mensajes(conversacion_id);
CREATE INDEX idx_mensajes_role ON mensajes(role);
CREATE INDEX idx_mensajes_created ON mensajes(created_at ASC);

COMMENT ON TABLE mensajes IS 'Mensajes del chat (user o assistant)';
COMMENT ON COLUMN mensajes.role IS 'user: mensaje del usuario, assistant: respuesta del LLM';

-- ============================================
-- SECCIÓN 11: TABLAS - MÓDULO MACHINE LEARNING
-- ============================================

-- Predicciones
CREATE TABLE predicciones (
    id SERIAL PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    componente_id INTEGER REFERENCES componentes(id) ON DELETE SET NULL,
    tipo tipo_prediccion NOT NULL,
    descripcion TEXT,
    confianza DECIMAL(5, 4) NOT NULL,
    nivel_confianza nivel_confianza NOT NULL,
    probabilidad_falla DECIMAL(5, 4),
    tiempo_estimado_dias INTEGER,
    fecha_estimada DATE,
    modelo_usado VARCHAR(100) DEFAULT 'llama3-local',
    version_modelo VARCHAR(50),
    datos_entrada JSONB,
    resultados JSONB,
    metricas JSONB,
    estado estado_prediccion DEFAULT 'pendiente',
    validada BOOLEAN DEFAULT FALSE,
    validada_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    validada_en TIMESTAMP,
    falla_relacionada_id INTEGER REFERENCES fallas(id) ON DELETE SET NULL,
    mantenimiento_relacionado_id INTEGER REFERENCES mantenimientos(id) ON DELETE SET NULL,
    notificacion_enviada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_confianza_valida CHECK (confianza BETWEEN 0 AND 1),
    CONSTRAINT chk_probabilidad_falla_valida CHECK (probabilidad_falla IS NULL OR probabilidad_falla BETWEEN 0 AND 1),
    CONSTRAINT chk_tiempo_estimado_positivo CHECK (tiempo_estimado_dias IS NULL OR tiempo_estimado_dias > 0)
);

CREATE INDEX idx_predicciones_moto ON predicciones(moto_id);
CREATE INDEX idx_predicciones_usuario ON predicciones(usuario_id);
CREATE INDEX idx_predicciones_componente ON predicciones(componente_id);
CREATE INDEX idx_predicciones_tipo ON predicciones(tipo);
CREATE INDEX idx_predicciones_estado ON predicciones(estado);
CREATE INDEX idx_predicciones_fecha_estimada ON predicciones(fecha_estimada);
CREATE INDEX idx_predicciones_created ON predicciones(created_at DESC);

COMMENT ON TABLE predicciones IS 'Predicciones ML de fallas, anomalías, mantenimiento';
COMMENT ON COLUMN predicciones.confianza IS 'Confianza del modelo: 0.0 a 1.0';

-- Entrenamientos de Modelos (MLOps básico)
CREATE TABLE entrenamientos_modelos (
    id SERIAL PRIMARY KEY,
    nombre_modelo VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    tipo_modelo tipo_modelo_ml NOT NULL,
    accuracy DECIMAL(5, 4),
    precision DECIMAL(5, 4),
    recall DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    mse DECIMAL(10, 4),
    rmse DECIMAL(10, 4),
    num_muestras_entrenamiento INTEGER,
    num_muestras_validacion INTEGER,
    num_muestras_test INTEGER,
    hiperparametros JSONB,
    features_usadas JSONB,
    duracion_entrenamiento_segundos DECIMAL(10, 2),
    fecha_inicio TIMESTAMP,
    fecha_fin TIMESTAMP,
    ruta_modelo VARCHAR(500),
    ruta_scaler VARCHAR(500),
    en_produccion BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    entrenado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    notas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT chk_metricas_validas CHECK (
        (accuracy IS NULL OR accuracy BETWEEN 0 AND 1) AND
        (precision IS NULL OR precision BETWEEN 0 AND 1) AND
        (recall IS NULL OR recall BETWEEN 0 AND 1) AND
        (f1_score IS NULL OR f1_score BETWEEN 0 AND 1)
    ),
    CONSTRAINT chk_muestras_positivas CHECK (
        (num_muestras_entrenamiento IS NULL OR num_muestras_entrenamiento > 0) AND
        (num_muestras_validacion IS NULL OR num_muestras_validacion >= 0) AND
        (num_muestras_test IS NULL OR num_muestras_test >= 0)
    ),
    CONSTRAINT chk_fecha_fin_posterior CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    CONSTRAINT uk_modelo_version UNIQUE (nombre_modelo, version)
);

CREATE INDEX idx_entrenamientos_nombre ON entrenamientos_modelos(nombre_modelo);
CREATE INDEX idx_entrenamientos_version ON entrenamientos_modelos(version);
CREATE INDEX idx_entrenamientos_tipo ON entrenamientos_modelos(tipo_modelo);
CREATE INDEX idx_entrenamientos_produccion ON entrenamientos_modelos(en_produccion) WHERE en_produccion = TRUE;
CREATE INDEX idx_entrenamientos_activo ON entrenamientos_modelos(activo) WHERE activo = TRUE;

COMMENT ON TABLE entrenamientos_modelos IS 'Tracking de entrenamientos de modelos ML (MLOps básico)';
COMMENT ON COLUMN entrenamientos_modelos.en_produccion IS 'TRUE si este modelo está activo en producción';

ALTER TABLE suscripciones ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE planes ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE motos ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE sensores ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE lecturas ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE mensajes ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE parametros ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE modelos_moto ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE plan_caracteristicas ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE caracteristicas ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE componentes ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE reglas_estado ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

ALTER TABLE mensajes ADD COLUMN tokens_usados INTEGER DEFAULT 0;
ALTER TABLE mensajes ADD COLUMN tiempo_respuesta_ms INTEGER DEFAULT 0;
ALTER TABLE mensajes ADD COLUMN modelo_usado VARCHAR;
-- ============================================
-- SECCIÓN 14: COMENTARIOS FINALES
-- ============================================

COMMENT ON DATABASE postgres IS 'RIM- MVP v2.3 - Sistema de Moto Inteligente con Gemelo Digital y Límites Freemium';

-- ============================================
-- FIN DEL SCRIPT
-- ============================================