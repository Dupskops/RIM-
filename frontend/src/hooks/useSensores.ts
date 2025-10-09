import { useQuery } from '@tanstack/react-query';
import { sensoresService } from '@/services';

export const useSensorReadings = (motoId: string, limit = 50) => {
  return useQuery({
    queryKey: ['sensor-readings', motoId, limit],
    queryFn: () => sensoresService.getRecentReadings(motoId, limit),
    enabled: !!motoId,
    refetchInterval: 5000, // Actualizar cada 5 segundos
  });
};

export const useLatestReadings = (motoId: string) => {
  return useQuery({
    queryKey: ['latest-readings', motoId],
    queryFn: () => sensoresService.getLatestReadings(motoId),
    enabled: !!motoId,
    refetchInterval: 3000, // Actualizar cada 3 segundos
  });
};

export const useSensorByType = (motoId: string, tipoSensor: string, limit = 100) => {
  return useQuery({
    queryKey: ['sensor-type', motoId, tipoSensor, limit],
    queryFn: () => sensoresService.getReadingsByType(motoId, tipoSensor, limit),
    enabled: !!motoId && !!tipoSensor,
  });
};
