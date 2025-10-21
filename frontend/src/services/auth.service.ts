import apiClient from '@/config/api-client';
import { API_ENDPOINTS } from '@/config/api-endpoints';
import type { AuthResponse, LoginRequest, RegisterRequest, User, TokenResponse } from '@/types';
import {
  getRefreshToken,
  clearAuthTokens,
  isAuthenticated,
  setAuthTokens,
} from '@/lib/auth-guard';

export const authService = {
  /**
   * Iniciar sesión
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials);

    // Guardar tokens usando función centralizada
    setAuthTokens(data.tokens.access_token, data.tokens.refresh_token);

    return data;
  },

  /**
   * Registrar nuevo usuario
   */
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const { data } = await apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.REGISTER, userData);

    // Guardar tokens usando función centralizada
    setAuthTokens(data.tokens.access_token, data.tokens.refresh_token);

    return data;
  },

  /**
   * Obtener perfil del usuario actual
   */
  async getProfile(): Promise<User> {
    const { data } = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
    return data;
  },

  /**
   * Actualizar perfil del usuario actual
   */
  async updateProfile(userData: Partial<User>): Promise<User> {
    const { data } = await apiClient.patch<User>(API_ENDPOINTS.AUTH.UPDATE_ME, userData);
    return data;
  },

  /**
   * Cerrar sesión
   */
  logout(): void {
    clearAuthTokens();
  },

  /**
   * Refrescar token
   */
  async refreshToken(): Promise<string> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token available');

    const { data } = await apiClient.post<TokenResponse>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refresh_token: refreshToken }
    );

    // Actualizar ambos tokens
    setAuthTokens(data.access_token, data.refresh_token);
    return data.access_token;
  },

  /**
   * Cambiar contraseña del usuario actual
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * Solicitar restablecimiento de contraseña
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.REQUEST_PASSWORD_RESET, { email });
  },

  /**
   * Restablecer contraseña con token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
      token,
      new_password: newPassword,
    });
  },

  /**
   * Verificar email con token
   */
  async verifyEmail(token: string): Promise<void> {
    await apiClient.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL, { token });
  },

  /**
   * Validar token de acceso
   */
  async validateToken(token?: string): Promise<boolean> {
    try {
      await apiClient.get(API_ENDPOINTS.AUTH.VALIDATE_TOKEN, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Verificar si el usuario está autenticado
   */
  isAuthenticated,
};
