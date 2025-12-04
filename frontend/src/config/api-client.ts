import axios, { type AxiosError, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios';
import { env } from './env';
import { getAccessToken, getRefreshToken, setAuthTokens, clearAuthTokens } from '@/lib/auth-guard';
import { AUTH_ENDPOINTS } from './api-endpoints';

// Cliente Axios configurado
const apiClient = axios.create({
  baseURL: env.API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 segundos (2 minutos) - para operaciones largas como el chatbot
});

// Variable para evitar múltiples intentos de refresh simultáneos
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

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

// Interceptor para manejar errores de autenticación y renovar token
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Si es un error 401 y no es el endpoint de refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Si ya estamos intentando renovar el token, agregar a la cola
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();

      if (!refreshToken) {
        // No hay refresh token, cerrar sesión
        clearAuthTokens();
        window.location.href = '/auth/login';
        return Promise.reject(error);
      }

      try {
        // Intentar renovar el token
        const response = await axios.post(
          `${env.API_URL}${AUTH_ENDPOINTS.REFRESH}`,
          { refresh_token: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' },
          }
        );

        const { access_token, refresh_token: new_refresh_token } = response.data;

        // Guardar los nuevos tokens
        setAuthTokens(access_token, new_refresh_token);

        // Procesar la cola de peticiones fallidas
        processQueue(null, access_token);

        // Reintentar la petición original con el nuevo token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        return apiClient(originalRequest);
      } catch (refreshError) {
        // Error al renovar el token, cerrar sesión
        processQueue(refreshError, null);
        clearAuthTokens();
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
