import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { env } from './env';
import { getAccessToken, clearAuthTokens } from '@/lib/auth-guard';

// Cliente Axios configurado
const apiClient = axios.create({
  baseURL: env.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 segundos
});

// Interceptor para agregar token JWT automáticamente
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      clearAuthTokens();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

