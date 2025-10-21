import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motosService } from '@/services';
import { useMotoStore } from '@/store';
import toast from 'react-hot-toast';

export const useMotos = () => {
  const { setMotos } = useMotoStore();

  return useQuery({
    queryKey: ['motos'],
    queryFn: async () => {
      const motos = await motosService.getMyMotos();
      setMotos(motos);
      return motos;
    },
  });
};

export const useMoto = (motoId: string) => {
  return useQuery({
    queryKey: ['moto', motoId],
    queryFn: () => motosService.getMotoById(motoId),
    enabled: !!motoId,
  });
};

export const useCreateMoto = () => {
  const queryClient = useQueryClient();
  const { addMoto } = useMotoStore();

  return useMutation({
    mutationFn: motosService.createMoto,
    onSuccess: (newMoto) => {
      queryClient.invalidateQueries({ queryKey: ['motos'] });
      addMoto(newMoto);
      toast.success('Moto registrada exitosamente');
    },
    onError: () => {
      toast.error('Error al registrar la moto');
    },
  });
};

export const useUpdateMoto = () => {
  const queryClient = useQueryClient();
  const { updateMoto } = useMotoStore();

  return useMutation({
    mutationFn: ({ motoId, data }: { motoId: string; data: Partial<any> }) =>
      motosService.updateMoto(motoId, data),
    onSuccess: (updatedMoto) => {
      queryClient.invalidateQueries({ queryKey: ['motos'] });
      queryClient.invalidateQueries({ queryKey: ['moto', updatedMoto.id] });
      updateMoto(updatedMoto);
      toast.success('Moto actualizada');
    },
    onError: () => {
      toast.error('Error al actualizar la moto');
    },
  });
};
