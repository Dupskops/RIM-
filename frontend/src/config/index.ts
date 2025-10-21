/**
 * Configuración centralizada del frontend
 */

export { default as apiClient } from './api-client';
export { env } from './env';
export { API_ENDPOINTS } from './api-endpoints';
export type {
  AuthEndpoint,
  UsuariosEndpoint,
  MotosEndpoint,
  SuscripcionesEndpoint,
  SensoresEndpoint,
  FallasEndpoint,
  MantenimientoEndpoint,
  MLEndpoint,
  ChatbotEndpoint,
  NotificacionesEndpoint,
} from './api-endpoints';
