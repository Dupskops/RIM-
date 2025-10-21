import apiClient from '@/config/api-client';
import type { SensorReading } from '@/types';

export const sensoresService = {
  /**
   * Obtener lecturas recientes de sensores
   */
  async getRecentReadings(motoId: string, limit = 50): Promise<SensorReading[]> {
    const { data } = await apiClient.get<SensorReading[]>(
      `/sensores/lecturas/${motoId}`,
      { params: { limit } }
    );
    return data;
  },

  /**
   * Obtener la última lectura de cada tipo de sensor
   */
  async getLatestReadings(motoId: string): Promise<SensorReading[]> {
    const { data } = await apiClient.get<SensorReading[]>(
      `/sensores/lecturas/latest/${motoId}`
    );
    return data;
  },

  /**
   * Obtener lecturas por tipo de sensor
   */
  async getReadingsByType(
    motoId: string,
    tipoSensor: string,
    limit = 100
  ): Promise<SensorReading[]> {
    const { data } = await apiClient.get<SensorReading[]>(
      `/sensores/lecturas/${motoId}/tipo/${tipoSensor}`,
      { params: { limit } }
    );
    return data;
  },

  /**
   * Simular lectura de sensores (para desarrollo/demo)
   */
  async simulateReading(motoId: string): Promise<SensorReading[]> {
    const { data } = await apiClient.post<SensorReading[]>(
      `/sensores/simular/${motoId}`
    );
    return data;
  },
};
