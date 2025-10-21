/**
 * Funciones de validación individual
 * Basado en: backend/src/auth/validators.py
 */

import * as v from 'valibot';
import { EmailSchema, PasswordSchema, NombreSchema, TelefonoSchema } from './schemas';

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Valida email y retorna resultado
 */
export const validateEmail = (email: string): ValidationResult => {
  try {
    v.parse(EmailSchema, email);
    return { isValid: true };
  } catch (error) {
    if (error instanceof v.ValiError) {
      return { isValid: false, error: error.issues[0]?.message };
    }
    return { isValid: false, error: 'Error de validación' };
  }
};

/**
 * Valida contraseña y retorna resultado
 */
export const validatePassword = (password: string): ValidationResult => {
  try {
    v.parse(PasswordSchema, password);
    return { isValid: true };
  } catch (error) {
    if (error instanceof v.ValiError) {
      return { isValid: false, error: error.issues[0]?.message };
    }
    return { isValid: false, error: 'Error de validación' };
  }
};

/**
 * Valida nombre y retorna resultado
 */
export const validateNombre = (nombre: string): ValidationResult => {
  try {
    v.parse(NombreSchema, nombre);
    return { isValid: true };
  } catch (error) {
    if (error instanceof v.ValiError) {
      return { isValid: false, error: error.issues[0]?.message };
    }
    return { isValid: false, error: 'Error de validación' };
  }
};

/**
 * Valida teléfono y retorna resultado
 */
export const validateTelefono = (telefono: string): ValidationResult => {
  try {
    v.parse(TelefonoSchema, telefono);
    return { isValid: true };
  } catch (error) {
    if (error instanceof v.ValiError) {
      return { isValid: false, error: error.issues[0]?.message };
    }
    return { isValid: false, error: 'Error de validación' };
  }
};

/**
 * Verifica si una contraseña cumple con cada requisito individual
 * Útil para mostrar feedback visual en tiempo real
 */
export const getPasswordRequirements = (password: string) => {
  return {
    minLength: password.length >= 8,
    hasUppercase: /[A-Z]/.test(password),
    hasLowercase: /[a-z]/.test(password),
    hasNumber: /\d/.test(password),
  };
};

/**
 * Verifica si todos los requisitos de contraseña se cumplen
 */
export const isPasswordValid = (password: string): boolean => {
  try {
    v.parse(PasswordSchema, password);
    return true;
  } catch {
    return false;
  }
};
