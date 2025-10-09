// ============================================
// Re-exports y adaptaciones de tipos del backend
// ============================================
// Los tipos base vienen de api.ts (generado automáticamente desde OpenAPI)
// Este archivo solo crea aliases convenientes y adaptaciones para el frontend

import type { components } from './api';

// ============================================
// ENTIDADES DEL BACKEND (alias convenientes)
// ============================================

/**
 * Usuario - Alias del tipo generado del backend
 */
export type User = components['schemas']['UsuarioResponse'];

/**
 * Token Response - Alias del tipo generado del backend
 */
export type TokenResponse = components['schemas']['TokenResponse'];

/**
 * Auth Response - Alias del tipo generado del backend
 * (En el backend se llama LoginResponse)
 */
export type AuthResponse = components['schemas']['LoginResponse'];

/**
 * Moto - Alias del tipo generado del backend
 */
export type Moto = components['schemas']['MotoResponse'];

/**
 * Lectura de Sensor - Alias del tipo generado del backend
 */
export type SensorReading = components['schemas']['LecturaSensorResponse'];

/**
 * Falla - Alias del tipo generado del backend
 */
export type Falla = components['schemas']['FallaResponse'];

/**
 * Mantenimiento - Alias del tipo generado del backend
 */
export type Mantenimiento = components['schemas']['MantenimientoResponse'];

/**
 * Notificación - Alias del tipo generado del backend
 */
export type Notificacion = components['schemas']['NotificacionResponse'];

/**
 * Predicción ML - Alias del tipo generado del backend
 */
export type Prediccion = components['schemas']['PrediccionResponse'];

// ============================================
// REQUESTS (para enviar al backend)
// ============================================

/**
 * Login Request - Alias del tipo generado del backend
 */
export type LoginRequest = components['schemas']['LoginRequest'];

/**
 * Register Request - Alias del tipo generado del backend
 */
export type RegisterRequest = components['schemas']['RegisterRequest'];

// ============================================
// TIPOS ADICIONALES SOLO PARA FRONTEND
// (No existen en el backend, son helpers de UI)
// ============================================

/**
 * Mensaje de chat (para UI del chatbot)
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    sensor_data?: SensorReading[];
    fallas?: Falla[];
  };
}

/**
 * Sesión de chat (para UI del chatbot)
 */
export interface ChatSession {
  id: string;
  moto_id: string;
  messages: ChatMessage[];
  created_at: string;
}

/**
 * Estadísticas del Dashboard (agregación de datos para UI)
 */
export interface DashboardStats {
  moto: Moto;
  estado_general: 'excelente' | 'bueno' | 'regular' | 'malo' | 'critico';
  sensores_actuales: SensorReading[];
  fallas_activas: number;
  proximo_mantenimiento?: Mantenimiento;
  predicciones_recientes: Prediccion[];
  notificaciones_sin_leer: number;
}

// ============================================
// RE-EXPORT de tipos generados (para conveniencia)
// ============================================

/**
 * Todos los schemas del backend
 */
export type { components } from './api';

/**
 * Todas las rutas del backend
 */
export type { paths } from './api';
