import apiClient from '@/config/api-client';
import type { Prediccion } from '@/types';

export const mlService = {
  /**
   * Obtener predicciones de la moto
   */
  async getPredicciones(motoId: string): Promise<Prediccion[]> {
    const { data } = await apiClient.get<Prediccion[]>(`/ml/predicciones/${motoId}`);
    return data;
  },

  /**
   * Ejecutar análisis predictivo
   */
  async analizarMoto(motoId: string): Promise<Prediccion[]> {
    const { data } = await apiClient.post<Prediccion[]>(`/ml/analizar/${motoId}`);
    return data;
  },

  /**
   * Obtener modelo de salud general
   */
  async getSaludGeneral(motoId: string): Promise<{
    score: number;
    estado: 'excelente' | 'bueno' | 'regular' | 'malo' | 'critico';
    factores: Record<string, number>;
  }> {
    const { data } = await apiClient.get(`/ml/salud/${motoId}`);
    return data;
  },
};
