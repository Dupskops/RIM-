import { redirect } from '@tanstack/react-router';

/**
 * Obtiene el token de acceso del localStorage
 * Esta es la única función que accede directamente a localStorage para leer access_token
 * @returns token de acceso o null
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Obtiene el refresh token del localStorage
 * Esta es la única función que accede directamente a localStorage para leer refresh_token
 * @returns refresh token o null
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem('refresh_token');
};

/**
 * Guarda los tokens de autenticación en localStorage
 * @param accessToken - Token de acceso JWT
 * @param refreshToken - Token de refresco
 */
export const setAuthTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

/**
 * Actualiza solo el access token (útil después de refresh)
 * @param accessToken - Nuevo token de acceso JWT
 */
export const setAccessToken = (accessToken: string): void => {
  localStorage.setItem('access_token', accessToken);
};

/**
 * Limpia los tokens de autenticación del localStorage
 */
export const clearAuthTokens = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

/**
 * Verifica si el usuario está autenticado
 * @returns true si hay token válido
 */
export const isAuthenticated = (): boolean => {
  return !!getAccessToken();
};

/**
 * Guard para proteger rutas que requieren autenticación
 * Redirige al login si no hay token
 */
export const requireAuth = () => {
  if (!isAuthenticated()) {
    throw redirect({ to: '/login' });
  }
};

/**
 * Guard para rutas de autenticación (login, register)
 * Redirige al dashboard si ya está autenticado
 */
export const requireGuest = () => {
  if (isAuthenticated()) {
    throw redirect({ to: '/app' });
  }
};
