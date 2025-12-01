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
  async getNotificacionesSinLeer(limit = 50): Promise<Notificacion[]> {
    const { data } = await apiClient.get('/notificaciones', {
      params: {
        solo_no_leidas: true,
        canal: 'in_app',   // 👈 igual que en getSiguienteNoLeida
        page: 1,
        per_page: limit,
      },
    });

    // Backend: { success, message, data: Notificacion[], pagination: {...} }
    const lista = data.data as Notificacion[];
    return lista;
  },


  async getSiguienteNoLeida(): Promise<Notificacion | null> {
  const { data } = await apiClient.get('/notificaciones', {
    params: {
      solo_no_leidas: true,
      canal: 'in_app',   // solo notificaciones del app
      page: 1,
      per_page: 1,
    },
  });

  // Backend devuelve un PaginatedResponse:
  // { success, message, data: Notificacion[], pagination: { ... } }
  const lista = data.data as Notificacion[];

  if (!lista || lista.length === 0) return null;
  return lista[0];
  },
  /**
   * Marcar notificación como leída
   */
   async marcarComoLeida(notificacionId: string): Promise<void> {
    await apiClient.patch('/notificaciones/leer', {
      // El esquema del backend es MarcarLeidaRequest:
      // notificacion_ids: Optional[list[int]]
      notificacion_ids: [Number(notificacionId)],
    });
  },

  /**
   * Marcar todas como leídas
   */
 async marcarTodasComoLeidas(): Promise<void> {
    // En tu backend, notificacion_ids = None significa "todas"
    await apiClient.patch('/notificaciones/leer', {});
  },

  /**
   * Eliminar notificación
   */
  async eliminarNotificacion(notificacionId: string): Promise<void> {
    await apiClient.delete(`/notificaciones/${notificacionId}`);
  },



  
};
