import apiClient from '@/config/api-client';
import type { Falla } from '@/types';

export const fallasService = {
  /**
   * Obtener todas las fallas de una moto
   */
  async getFallas(motoId: string): Promise<Falla[]> {
    const { data } = await apiClient.get<Falla[]>(`/fallas/moto/${motoId}`);
    return data;
  },

  /**
   * Obtener fallas activas
   */
  async getActiveFallas(motoId: string): Promise<Falla[]> {
    const { data } = await apiClient.get<Falla[]>(`/fallas/moto/${motoId}/activas`);
    return data;
  },

  /**
   * Obtener una falla específica
   */
  async getFallaById(fallaId: string): Promise<Falla> {
    const { data } = await apiClient.get<Falla>(`/fallas/${fallaId}`);
    return data;
  },

  /**
   * Marcar falla como resuelta
   */
  async resolveFalla(fallaId: string, notas?: string): Promise<Falla> {
    const { data } = await apiClient.put<Falla>(`/fallas/${fallaId}/resolver`, { notas });
    return data;
  },

  /**
   * Detectar anomalías en los sensores
   */
  async detectAnomalias(motoId: string): Promise<Falla[]> {
    const { data } = await apiClient.post<Falla[]>(`/fallas/detectar/${motoId}`);
    return data;
  },
};
