import { useQuery } from '@tanstack/react-query';
import { fallasService } from '@/services';

export const useFallas = (motoId: string) => {
  return useQuery({
    queryKey: ['fallas', motoId],
    queryFn: () => fallasService.getFallas(motoId),
    enabled: !!motoId,
  });
};

export const useActiveFallas = (motoId: string) => {
  return useQuery({
    queryKey: ['fallas-activas', motoId],
    queryFn: () => fallasService.getActiveFallas(motoId),
    enabled: !!motoId,
    refetchInterval: 10000, // Actualizar cada 10 segundos
  });
};
