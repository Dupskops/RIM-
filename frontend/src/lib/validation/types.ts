/**
 * Tipos e interfaces para validación
 */

import * as v from 'valibot';
import { RegisterSchemaWithConfirm, LoginSchema } from './schemas';

/**
 * Tipo inferido del schema de registro
 */
export type RegisterFormData = v.InferInput<typeof RegisterSchemaWithConfirm>;

/**
 * Tipo inferido del schema de login
 */
export type LoginFormData = v.InferInput<typeof LoginSchema>;

/**
 * Resultado de validación genérico
 */
export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Requisitos de contraseña para UI
 */
export interface PasswordRequirements {
  minLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
}
