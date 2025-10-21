import apiClient from '@/config/api-client';
import type { Notificacion } from '@/types';

export const notificacionesService = {
  /**
   * Obtener todas las notificaciones del usuario
   */
  async getNotificaciones(limit = 50): Promise<Notificacion[]> {
    const { data } = await apiClient.get<Notificacion[]>('/notificaciones', {
      params: { limit },
    });
    return data;
  },

  /**
   * Obtener notificaciones sin leer
   */
  async getNotificacionesSinLeer(): Promise<Notificacion[]> {
    const { data } = await apiClient.get<Notificacion[]>('/notificaciones/sin-leer');
    return data;
  },

  /**
   * Marcar notificación como leída
   */
  async marcarComoLeida(notificacionId: string): Promise<void> {
    await apiClient.put(`/notificaciones/${notificacionId}/leer`);
  },

  /**
   * Marcar todas como leídas
   */
  async marcarTodasComoLeidas(): Promise<void> {
    await apiClient.put('/notificaciones/leer-todas');
  },

  /**
   * Eliminar notificación
   */
  async eliminarNotificacion(notificacionId: string): Promise<void> {
    await apiClient.delete(`/notificaciones/${notificacionId}`);
  },
};
