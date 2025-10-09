// Configuración de variables de entorno
export const env = {
  // API Backend
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:4000/api',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:4000',
  
  // Configuración de la aplicación
  APP_NAME: 'RIM - Sistema Inteligente de Moto',
  APP_VERSION: '1.0.0',
  
  // Feature flags
  ENABLE_3D_MODEL: import.meta.env.VITE_ENABLE_3D_MODEL !== 'false',
  ENABLE_CHATBOT: import.meta.env.VITE_ENABLE_CHATBOT !== 'false',
  ENABLE_NOTIFICATIONS: import.meta.env.VITE_ENABLE_NOTIFICATIONS !== 'false',
  
  // Desarrollo
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.MODE === 'production',
} as const;
