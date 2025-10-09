import apiClient from '@/config/api-client';
import type { Mantenimiento } from '@/types';

export const mantenimientoService = {
  /**
   * Obtener todos los mantenimientos de una moto
   */
  async getMantenimientos(motoId: string): Promise<Mantenimiento[]> {
    const { data } = await apiClient.get<Mantenimiento[]>(`/mantenimiento/moto/${motoId}`);
    return data;
  },

  /**
   * Obtener próximo mantenimiento programado
   */
  async getProximoMantenimiento(motoId: string): Promise<Mantenimiento | null> {
    const { data } = await apiClient.get<Mantenimiento | null>(
      `/mantenimiento/moto/${motoId}/proximo`
    );
    return data;
  },

  /**
   * Crear nuevo mantenimiento
   */
  async createMantenimiento(
    mantenimientoData: Omit<Mantenimiento, 'id' | 'fecha_realizada'>
  ): Promise<Mantenimiento> {
    const { data } = await apiClient.post<Mantenimiento>(
      '/mantenimiento',
      mantenimientoData
    );
    return data;
  },

  /**
   * Marcar mantenimiento como completado
   */
  async completarMantenimiento(mantenimientoId: string, notas?: string): Promise<Mantenimiento> {
    const { data } = await apiClient.put<Mantenimiento>(
      `/mantenimiento/${mantenimientoId}/completar`,
      { notas }
    );
    return data;
  },

  /**
   * Cancelar mantenimiento
   */
  async cancelarMantenimiento(mantenimientoId: string): Promise<void> {
    await apiClient.delete(`/mantenimiento/${mantenimientoId}`);
  },
};
