import apiClient from '@/config/api-client';
import { API_ENDPOINTS } from '@/config/api-endpoints';
import type { Moto } from '@/types';

export const motosService = {
  /**
   * Obtener todas las motos del usuario
   */
  async getMyMotos(): Promise<Moto[]> {
    const resp = await apiClient.get(API_ENDPOINTS.MOTOS.BASE);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Obtener una moto por ID
   */
  async getMotoById(motoId: string): Promise<Moto> {
    const resp = await apiClient.get(API_ENDPOINTS.MOTOS.BY_ID(motoId));
    return resp.data?.data ?? resp.data;
  },

  /**
   * Registrar una nueva moto
   */
  async createMoto(motoData: Omit<Moto, 'id' | 'usuario_id' | 'created_at'>): Promise<Moto> {
    const resp = await apiClient.post(API_ENDPOINTS.MOTOS.BASE, motoData);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Actualizar información de la moto
   */
  async updateMoto(motoId: string, motoData: Partial<Moto>): Promise<Moto> {
    const resp = await apiClient.put(API_ENDPOINTS.MOTOS.BY_ID(motoId), motoData);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Eliminar una moto
   */
  async deleteMoto(motoId: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.MOTOS.BY_ID(motoId));
  },
};
