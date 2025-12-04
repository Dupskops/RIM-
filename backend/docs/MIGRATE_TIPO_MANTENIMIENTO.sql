-- ============================================
-- Script: Actualizar ENUM tipo_mantenimiento
-- Descripción: Reemplaza el enum genérico con tipos específicos
-- NOTA: Solo funciona si la tabla mantenimientos está vacía
-- ============================================
-- Paso 1: Eliminar la columna que usa el enum
ALTER TABLE mantenimientos DROP COLUMN tipo;
-- Paso 2: Eliminar el enum antiguo
DROP TYPE tipo_mantenimiento;
-- Paso 3: Crear el nuevo enum con valores específicos
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
-- Paso 4: Volver a agregar la columna con el nuevo enum
ALTER TABLE mantenimientos
ADD COLUMN tipo tipo_mantenimiento NOT NULL;
-- Paso 5: Recrear el índice
CREATE INDEX idx_mantenimientos_tipo ON mantenimientos(tipo);
-- Verificar los cambios
SELECT enumlabel as valor_enum
FROM pg_enum
WHERE enumtypid = 'tipo_mantenimiento'::regtype
ORDER BY enumsortorder;
COMMENT ON TYPE tipo_mantenimiento IS 'Tipos específicos de mantenimiento según src/shared/constants.py';