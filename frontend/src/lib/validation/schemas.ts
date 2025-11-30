/**
 * Schemas de validación usando Valibot
 * Basado en: backend/src/auth/validators.py
 */

import * as v from 'valibot';

/**
 * Schema de validación para email
 */
export const EmailSchema = v.pipe(
  v.string('El email es requerido'),
  v.nonEmpty('El email no puede estar vacío'),
  v.email('Formato de email inválido'),
);

/**
 * Schema de validación para contraseña
 * Requisitos:
 * - Mínimo 8 caracteres
 * - Al menos una mayúscula
 * - Al menos una minúscula
 * - Al menos un número
 */
export const PasswordSchema = v.pipe(
  v.string('La contraseña es requerida'),
  v.nonEmpty('La contraseña no puede estar vacía'),
  v.minLength(8, 'La contraseña debe tener al menos 8 caracteres'),
  v.regex(/[A-Z]/, 'La contraseña debe contener al menos una mayúscula'),
  v.regex(/[a-z]/, 'La contraseña debe contener al menos una minúscula'),
  v.regex(/\d/, 'La contraseña debe contener al menos un número'),
);

/**
 * Schema de validación para nombre
 * Requisitos:
 * - Mínimo 2 caracteres
 * - Máximo 255 caracteres
 * - Solo letras y espacios
 */
export const NombreSchema = v.pipe(
  v.string('El nombre es requerido'),
  v.nonEmpty('El nombre no puede estar vacío'),
  v.minLength(2, 'El nombre debe tener al menos 2 caracteres'),
  v.maxLength(255, 'El nombre no puede exceder 255 caracteres'),
  v.regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'El nombre solo puede contener letras y espacios'),
);

/**
 * Schema de validación para apellido
 * Requisitos:
 * - Mínimo 2 caracteres
 * - Máximo 255 caracteres
 * - Solo letras y espacios
 */
export const ApellidoSchema = v.pipe(
  v.string('El apellido es requerido'),
  v.nonEmpty('El apellido no puede estar vacío'),
  v.minLength(2, 'El apellido debe tener al menos 2 caracteres'),
  v.maxLength(255, 'El apellido no puede exceder 255 caracteres'),
  v.regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'El apellido solo puede contener letras y espacios'),
);

/**
 * Schema de validación para teléfono
 * Formato: +[código país][número] (8-15 dígitos)
 */
export const TelefonoSchema = v.pipe(
  v.string('El teléfono debe ser texto'),
  v.transform((input) => input.replace(/[\s-]/g, '')), // Limpiar espacios y guiones
  v.regex(/^\+?\d{8,15}$/, 'Formato de teléfono inválido. Debe contener entre 8 y 15 dígitos'),
);

/**
 * Schema de validación para teléfono opcional
 */
export const TelefonoOptionalSchema = v.optional(
  v.union([
    v.pipe(v.literal(''), v.transform(() => undefined)),
    TelefonoSchema,
  ])
);

/**
 * Schema completo para registro de usuario
 */
export const RegisterSchema = v.object({
  nombre: NombreSchema,
  apellido: ApellidoSchema,
  email: EmailSchema,
  telefono: TelefonoOptionalSchema,
  password: PasswordSchema,
  confirmPassword: v.string('Confirma tu contraseña'),
});

/**
 * Schema con validación de coincidencia de contraseñas
 */
export const RegisterSchemaWithConfirm = v.pipe(
  RegisterSchema,
  v.forward(
    v.partialCheck(
      [['password'], ['confirmPassword']],
      (input) => input.password === input.confirmPassword,
      'Las contraseñas no coinciden'
    ),
    ['confirmPassword']
  )
);

/**
 * Schema para login
 */
export const LoginSchema = v.object({
  email: EmailSchema,
  password: v.pipe(
    v.string('La contraseña es requerida'),
    v.nonEmpty('La contraseña no puede estar vacía'),
  ),
});
