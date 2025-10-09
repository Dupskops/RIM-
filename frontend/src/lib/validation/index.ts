/**
 * Barrel export para módulo de validación
 */

// Schemas
export {
  EmailSchema,
  PasswordSchema,
  NombreSchema,
  TelefonoSchema,
  TelefonoOptionalSchema,
  RegisterSchema,
  RegisterSchemaWithConfirm,
  LoginSchema,
} from './schemas';

// Validators
export {
  validateEmail,
  validatePassword,
  validateNombre,
  validateTelefono,
  getPasswordRequirements,
  isPasswordValid,
} from './validators';

// Types
export type {
  RegisterFormData,
  LoginFormData,
  ValidationResult,
  PasswordRequirements,
} from './types';
