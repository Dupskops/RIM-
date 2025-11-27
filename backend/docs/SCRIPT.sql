-- ##################################################################
-- ### INICIO DEL SCRIPT SQL PARA "KTM DIGITAL TWIN" (PostgreSQL) ###
-- ##################################################################
-- ==================================================================
-- MÓDULO 0: DEFINICIÓN DE TIPOS (ENUMs)
-- ==================================================================
-- Estos tipos se deben crear primero.
CREATE TYPE logica_regla AS ENUM('MAYOR_QUE', 'MENOR_QUE', 'ENTRE');

CREATE TYPE estado_salud AS ENUM('EXCELENTE', 'BUENO', 'ATENCION', 'CRITICO');

CREATE TYPE nivel_prioridad AS ENUM('BAJA', 'MEDIA', 'ALTA');

CREATE TYPE canal_notificacion AS ENUM('PUSH', 'EMAIL', 'SMS');

CREATE TYPE rol_chat AS ENUM('USUARIO', 'LLM');

CREATE TYPE periodo_plan AS ENUM('MENSUAL', 'ANUAL', 'UNICO');

CREATE TYPE estado_suscripcion AS ENUM('ACTIVA', 'CANCELADA', 'PENDIENTE_PAGO');

-- ==================================================================
-- MÓDULO 1: AUTENTICACIÓN Y USUARIOS
-- ==================================================================
-- (Basado en tu arquitectura)
CREATE TABLE
  usuarios (
    id serial PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255),
    telefono VARCHAR(20),
    email_verificado BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    rol VARCHAR(20) NOT NULL DEFAULT 'USER', -- ej: 'USER', 'ADMIN'
    ultimo_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
  );

CREATE INDEX ix_usuarios_id ON usuarios (id);

CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);

CREATE INDEX ix_usuarios_rol ON usuarios (rol);

CREATE TABLE
  email_verification_tokens (
    id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    usado_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
  );

CREATE INDEX ix_email_verification_tokens_id ON email_verification_tokens (id);

CREATE INDEX ix_email_verification_tokens_usuario_id ON email_verification_tokens (usuario_id);

CREATE UNIQUE INDEX ix_email_verification_tokens_token ON email_verification_tokens (token);

CREATE TABLE
  password_reset_tokens (
    id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    usado_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
  );

CREATE INDEX ix_password_reset_tokens_id ON password_reset_tokens (id);

CREATE INDEX ix_password_reset_tokens_usuario_id ON password_reset_tokens (usuario_id);

CREATE UNIQUE INDEX ix_password_reset_tokens_token ON password_reset_tokens (token);

CREATE TABLE
  refresh_tokens (
    id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revocado BOOLEAN NOT NULL DEFAULT FALSE,
    revocado_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
  );

CREATE INDEX ix_refresh_tokens_id ON refresh_tokens (id);

CREATE INDEX ix_refresh_tokens_usuario_id ON refresh_tokens (usuario_id);

CREATE UNIQUE INDEX ix_refresh_tokens_token ON refresh_tokens (token);

-- ==================================================================
-- MÓDULO 2: FREEMIUM Y SUSCRIPCIONES
-- ==================================================================
CREATE TABLE
  planes (
    id serial PRIMARY KEY,
    nombre_plan VARCHAR(100) NOT NULL UNIQUE,
    precio DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    periodo_facturacion periodo_plan NOT NULL DEFAULT 'UNICO',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE TABLE
  caracteristicas (
    id serial PRIMARY KEY,
    clave_funcion VARCHAR(100) NOT NULL UNIQUE, -- ej: "CHAT_LLM", "PREDICCION_ML"
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE TABLE
  plan_caracteristicas (
    plan_id INTEGER NOT NULL REFERENCES planes (id) ON DELETE CASCADE,
    caracteristica_id INTEGER NOT NULL REFERENCES caracteristicas (id) ON DELETE CASCADE,
    PRIMARY KEY (plan_id, caracteristica_id)
  );

CREATE TABLE
  suscripciones_usuario (
    id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL UNIQUE REFERENCES usuarios (id) ON DELETE CASCADE,
    plan_id INTEGER NOT NULL REFERENCES planes (id) ON DELETE RESTRICT, -- No borrar un plan si usuarios lo tienen
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_fin TIMESTAMP WITH TIME ZONE, -- Nulo si es vitalicio o 'Free'
    estado_suscripcion estado_suscripcion NOT NULL, -- 'ACTIVA', 'CANCELADA'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_suscripciones_usuario_usuario_id ON suscripciones_usuario (usuario_id);

CREATE INDEX ix_suscripciones_usuario_plan_id ON suscripciones_usuario (plan_id);

-- ==================================================================
-- MÓDULO 3: NÚCLEO DE LA APP (GEMELO DIGITAL)
-- ==================================================================
CREATE TABLE
  motos (
    moto_id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    vin VARCHAR(17) UNIQUE,
    modelo VARCHAR(100) NOT NULL DEFAULT 'KTM 390 Duke',
    ano INTEGER NOT NULL,
    placa VARCHAR(20) UNIQUE,
    color VARCHAR(50),
    kilometraje_actual DECIMAL(10, 2) NOT NULL DEFAULT 0.0,
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_motos_usuario_id ON motos (usuario_id);

CREATE UNIQUE INDEX ix_motos_vin ON motos (vin);

CREATE UNIQUE INDEX ix_motos_placa ON motos (placa);

CREATE TABLE
  componentes (
    componente_id serial PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    mesh_id_3d VARCHAR(100) UNIQUE, -- ej: "engine_block"
    descripcion TEXT
  );

CREATE TABLE
  parametros (
    parametro_id serial PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE, -- ej: "Temperatura Motor"
    unidad_medida VARCHAR(20) -- ej: "°C", "bar", "mm"
  );

CREATE TABLE
  reglas_estado (
    regla_id serial PRIMARY KEY,
    componente_id INTEGER NOT NULL REFERENCES componentes (componente_id) ON DELETE CASCADE,
    parametro_id INTEGER NOT NULL REFERENCES parametros (parametro_id) ON DELETE CASCADE,
    logica logica_regla NOT NULL,
    limite_bueno DECIMAL(10, 2), -- Límite entre Bueno y Excelente
    limite_atencion DECIMAL(10, 2), -- Límite entre Atención y Bueno
    limite_critico DECIMAL(10, 2), -- Límite entre Crítico y Atención
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE (componente_id, parametro_id) -- Solo una regla por comb.
  );

CREATE INDEX ix_reglas_estado_componente_id ON reglas_estado (componente_id);

CREATE INDEX ix_reglas_estado_parametro_id ON reglas_estado (parametro_id);

CREATE TABLE
  historial_lecturas (
    lectura_id serial PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos (moto_id) ON DELETE CASCADE,
    parametro_id INTEGER NOT NULL REFERENCES parametros (parametro_id) ON DELETE RESTRICT,
    valor DECIMAL(10, 3) NOT NULL,
    TIMESTAMP TIMESTAMP WITH TIME ZONE NOT NULL
  );

-- Índices cruciales para analíticas y ML
CREATE INDEX ix_historial_lecturas_moto_id_timestamp ON historial_lecturas (moto_id, TIMESTAMP DESC);

CREATE INDEX ix_historial_lecturas_parametro_id ON historial_lecturas (parametro_id);

CREATE TABLE
  estado_actual (
    estado_actual_id serial PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos (moto_id) ON DELETE CASCADE,
    componente_id INTEGER NOT NULL REFERENCES componentes (componente_id) ON DELETE CASCADE,
    ultimo_valor DECIMAL(10, 3),
    estado estado_salud NOT NULL,
    ultima_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE (moto_id, componente_id) -- Clave para INSERT ... ON CONFLICT UPDATE
  );

CREATE INDEX ix_estado_actual_moto_id ON estado_actual (moto_id);

-- ==================================================================
-- MÓDULO 4: CARACTERÍSTICAS (IA, VIAJES, CHAT)
-- ==================================================================
CREATE TABLE
  viajes (
    viaje_id serial PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos (moto_id) ON DELETE CASCADE,
    timestamp_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    timestamp_fin TIMESTAMP WITH TIME ZONE,
    distancia_km DECIMAL(10, 2),
    velocidad_media_kmh DECIMAL(5, 2),
    kilometraje_inicio DECIMAL(10, 2),
    kilometraje_fin DECIMAL(10, 2)
  );

CREATE INDEX ix_viajes_moto_id ON viajes (moto_id);

CREATE TABLE
  predicciones_ml (
    prediccion_id serial PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos (moto_id) ON DELETE CASCADE,
    componente_id INTEGER NOT NULL REFERENCES componentes (componente_id) ON DELETE CASCADE,
    mensaje_prediccion TEXT NOT NULL,
    km_predichos INTEGER, -- ej: Fallo predicho en 850km
    TIMESTAMP TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_predicciones_ml_moto_id ON predicciones_ml (moto_id);

CREATE INDEX ix_predicciones_ml_componente_id ON predicciones_ml (componente_id);

CREATE TABLE
  insights_llm (
    insight_id serial PRIMARY KEY,
    moto_id INTEGER NOT NULL REFERENCES motos (moto_id) ON DELETE CASCADE,
    resumen_generado TEXT NOT NULL,
    prioridad nivel_prioridad NOT NULL DEFAULT 'BAJA',
    TIMESTAMP TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_insights_llm_moto_id ON insights_llm (moto_id);

CREATE TABLE
  notificaciones (
    notificacion_id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    mensaje TEXT NOT NULL,
    canal canal_notificacion NOT NULL,
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    TIMESTAMP TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_notificaciones_usuario_id ON notificaciones (usuario_id);

CREATE TABLE
  chat_sesiones (
    sesion_id serial PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    moto_id INTEGER REFERENCES motos (moto_id) ON DELETE SET NULL, -- Un chat puede no estar ligado a una moto
    titulo VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_chat_sesiones_usuario_id ON chat_sesiones (usuario_id);

CREATE INDEX ix_chat_sesiones_moto_id ON chat_sesiones (moto_id);

CREATE TABLE
  chat_historial (
    mensaje_id serial PRIMARY KEY,
    sesion_id INTEGER NOT NULL REFERENCES chat_sesiones (sesion_id) ON DELETE CASCADE,
    rol rol_chat NOT NULL,
    mensaje TEXT NOT NULL,
    TIMESTAMP TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
  );

CREATE INDEX ix_chat_historial_sesion_id ON chat_historial (sesion_id);

-- ################################################################
-- ### FIN DEL SCRIPT SQL
-- ################################################################