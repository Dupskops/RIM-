/**
 * Constantes de endpoints de la API
 * Centraliza todas las rutas de la API para facilitar mantenimiento y refactoring
 */

/**
 * Helper para construir URLs con parámetros
 */
const buildUrl = (path: string, params?: Record<string, string | number>): string => {
  if (!params) return path;

  let url = path;
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`{${key}}`, String(value));
  });
  return url;
};

/**
 * Endpoints de Autenticación
 */
export const AUTH_ENDPOINTS = {
  REGISTER: '/auth/register',
  LOGIN: '/auth/login',
  REFRESH: '/auth/refresh',
  LOGOUT: '/auth/logout',
  CHANGE_PASSWORD: '/auth/change-password',
  REQUEST_PASSWORD_RESET: '/auth/request-password-reset',
  RESET_PASSWORD: '/auth/reset-password',
  VERIFY_EMAIL: '/auth/verify-email',
  ME: '/auth/me',
  UPDATE_ME: '/auth/me', // PATCH - Actualizar perfil
  VALIDATE_TOKEN: '/auth/validate-token',
} as const;

/**
 * Endpoints de Usuarios
 */
export const USUARIOS_ENDPOINTS = {
  BASE: '/usuarios',
  STATS: '/usuarios/stats',
  BY_ID: (id: string | number) => buildUrl('/usuarios/{usuario_id}', { usuario_id: id }),
  UPDATE: (id: string | number) => buildUrl('/usuarios/{usuario_id}', { usuario_id: id }), // PATCH
  DELETE: (id: string | number) => buildUrl('/usuarios/{usuario_id}', { usuario_id: id }),
  DEACTIVATE: (id: string | number) => buildUrl('/usuarios/{usuario_id}/deactivate', { usuario_id: id }),
  ACTIVATE: (id: string | number) => buildUrl('/usuarios/{usuario_id}/activate', { usuario_id: id }),
} as const;

/**
 * Endpoints de Motos
 */
export const MOTOS_ENDPOINTS = {
  BASE: '/motos/',
  MODELOS_DISPONIBLES: '/motos/modelos-disponibles',
  STATS: '/motos/stats',
  BY_ID: (id: string | number) => buildUrl('/motos/{moto_id}', { moto_id: id }),
  UPDATE: (id: string | number) => buildUrl('/motos/{moto_id}', { moto_id: id }), // PATCH
  DELETE: (id: string | number) => buildUrl('/motos/{moto_id}', { moto_id: id }),
  KILOMETRAJE: (id: string | number) => buildUrl('/motos/{moto_id}/kilometraje', { moto_id: id }), // PATCH
} as const;

/**
 * Endpoints de Suscripciones
 */
export const SUSCRIPCIONES_ENDPOINTS = {
  BASE: '/suscripciones/',
  ME: '/suscripciones/me',
  STATS: '/suscripciones/stats',
  BY_ID: (id: string | number) => buildUrl('/suscripciones/{suscripcion_id}', { suscripcion_id: id }),
  UPGRADE: '/suscripciones/upgrade',
  CANCEL: '/suscripciones/cancel',
  RENEW: '/suscripciones/renew',
} as const;

/**
 * Endpoints de Sensores
 */
export const SENSORES_ENDPOINTS = {
  BASE: '/sensores/',
  LECTURAS: '/sensores/lecturas',
  STATS: '/sensores/stats',
} as const;

/**
 * Endpoints de Fallas
 */
export const FALLAS_ENDPOINTS = {
  BASE: '/fallas/',
  ML: '/fallas/ml',
  BY_ID: (id: string | number) => buildUrl('/fallas/{falla_id}', { falla_id: id }),
  UPDATE: (id: string | number) => buildUrl('/fallas/{falla_id}', { falla_id: id }), // PATCH
  DELETE: (id: string | number) => buildUrl('/fallas/{falla_id}', { falla_id: id }),
  BY_MOTO: (motoId: string | number) => buildUrl('/fallas/moto/{moto_id}', { moto_id: motoId }),
  DIAGNOSTICAR: (id: string | number) => buildUrl('/fallas/{falla_id}/diagnosticar', { falla_id: id }),
  RESOLVER: (id: string | number) => buildUrl('/fallas/{falla_id}/resolver', { falla_id: id }),
  STATS_BY_MOTO: (motoId: string | number) => buildUrl('/fallas/moto/{moto_id}/stats', { moto_id: motoId }),
} as const;

/**
 * Endpoints de Mantenimiento
 */
export const MANTENIMIENTO_ENDPOINTS = {
  BASE: '/mantenimiento/',
  ML: '/mantenimiento/ml',
  BY_ID: (id: string | number) => buildUrl('/mantenimiento/{mantenimiento_id}', { mantenimiento_id: id }),
  UPDATE: (id: string | number) => buildUrl('/mantenimiento/{mantenimiento_id}', { mantenimiento_id: id }), // PATCH
  DELETE: (id: string | number) => buildUrl('/mantenimiento/{mantenimiento_id}', { mantenimiento_id: id }),
  BY_MOTO: (motoId: string | number) => buildUrl('/mantenimiento/moto/{moto_id}', { moto_id: motoId }),
  INICIAR: (id: string | number) => buildUrl('/mantenimiento/{mantenimiento_id}/iniciar', { mantenimiento_id: id }),
  COMPLETAR: (id: string | number) => buildUrl('/mantenimiento/{mantenimiento_id}/completar', { mantenimiento_id: id }),
  STATS_BY_MOTO: (motoId: string | number) => buildUrl('/mantenimiento/moto/{moto_id}/stats', { moto_id: motoId }),
} as const;

/**
 * Endpoints de Machine Learning
 */
export const ML_ENDPOINTS = {
  PREDICT_FAULT: '/ml/predict/fault',
  PREDICT_ANOMALY: '/ml/predict/anomaly',
  VALIDATE_PREDICTION: (id: string | number) => buildUrl('/ml/predictions/{prediccion_id}/validate', { prediccion_id: id }),
  BY_MOTO: (motoId: string | number) => buildUrl('/ml/predictions/moto/{moto_id}', { moto_id: motoId }),
  BY_USUARIO: (usuarioId: string | number) => buildUrl('/ml/predictions/usuario/{usuario_id}', { usuario_id: usuarioId }),
  CRITICAS: '/ml/predictions/criticas',
  STATISTICS: '/ml/statistics',
  MODEL_INFO: (modelName: string) => buildUrl('/ml/models/{nombre_modelo}/info', { nombre_modelo: modelName }),
  MODELS_STATUS: '/ml/models/status',
} as const;

/**
 * Endpoints de Chatbot
 */
export const CHATBOT_ENDPOINTS = {
  BASE: '/chatbot/',
  CHAT: '/chatbot/chat',
  CHAT_STREAM: '/chatbot/chat-stream',
  BY_ID: (id: string | number) => buildUrl('/chatbot/{conversation_id}', { conversation_id: id }),
  DELETE: (id: string | number) => buildUrl('/chatbot/{conversation_id}', { conversation_id: id }),
  BY_USUARIO: (usuarioId: string | number) => buildUrl('/chatbot/usuario/{usuario_id}', { usuario_id: usuarioId }),
  MESSAGE_FEEDBACK: (msgId: string | number) => buildUrl('/chatbot/messages/{mensaje_id}/feedback', { mensaje_id: msgId }),
  CLEAR_HISTORY: (conversationId: string | number) => buildUrl('/chatbot/{conversation_id}/history', { conversation_id: conversationId }), // DELETE
  STATS_SUMMARY: '/chatbot/stats/summary',
} as const;

/**
 * Endpoints de Notificaciones
 */
export const NOTIFICACIONES_ENDPOINTS = {
  BASE: '/notificaciones',
  MASIVA: '/notificaciones/masiva',
  BY_ID: (id: string | number) => buildUrl('/notificaciones/{notificacion_id}', { notificacion_id: id }),
  DELETE: (id: string | number) => buildUrl('/notificaciones/{notificacion_id}', { notificacion_id: id }),
  LEER: '/notificaciones/leer', // PATCH
  STATS: '/notificaciones/stats',
  PREFERENCIAS: '/notificaciones/preferencias', // GET y PUT
} as const;

/**
 * Endpoints Generales
 */
export const GENERAL_ENDPOINTS = {
  STATUS: '/status',
} as const;

/**
 * Objeto unificado con todos los endpoints
 */
export const API_ENDPOINTS = {
  AUTH: AUTH_ENDPOINTS,
  USUARIOS: USUARIOS_ENDPOINTS,
  MOTOS: MOTOS_ENDPOINTS,
  SUSCRIPCIONES: SUSCRIPCIONES_ENDPOINTS,
  SENSORES: SENSORES_ENDPOINTS,
  FALLAS: FALLAS_ENDPOINTS,
  MANTENIMIENTO: MANTENIMIENTO_ENDPOINTS,
  ML: ML_ENDPOINTS,
  CHATBOT: CHATBOT_ENDPOINTS,
  NOTIFICACIONES: NOTIFICACIONES_ENDPOINTS,
  GENERAL: GENERAL_ENDPOINTS,
} as const;

/**
 * Type helpers para TypeScript
 */
export type AuthEndpoint = (typeof AUTH_ENDPOINTS)[keyof typeof AUTH_ENDPOINTS];
export type UsuariosEndpoint = (typeof USUARIOS_ENDPOINTS)[keyof typeof USUARIOS_ENDPOINTS];
export type MotosEndpoint = (typeof MOTOS_ENDPOINTS)[keyof typeof MOTOS_ENDPOINTS];
export type SuscripcionesEndpoint = (typeof SUSCRIPCIONES_ENDPOINTS)[keyof typeof SUSCRIPCIONES_ENDPOINTS];
export type SensoresEndpoint = (typeof SENSORES_ENDPOINTS)[keyof typeof SENSORES_ENDPOINTS];
export type FallasEndpoint = (typeof FALLAS_ENDPOINTS)[keyof typeof FALLAS_ENDPOINTS];
export type MantenimientoEndpoint = (typeof MANTENIMIENTO_ENDPOINTS)[keyof typeof MANTENIMIENTO_ENDPOINTS];
export type MLEndpoint = (typeof ML_ENDPOINTS)[keyof typeof ML_ENDPOINTS];
export type ChatbotEndpoint = (typeof CHATBOT_ENDPOINTS)[keyof typeof CHATBOT_ENDPOINTS];
export type NotificacionesEndpoint = (typeof NOTIFICACIONES_ENDPOINTS)[keyof typeof NOTIFICACIONES_ENDPOINTS];

/**
 * Export default para uso simplificado
 */
export default API_ENDPOINTS;
