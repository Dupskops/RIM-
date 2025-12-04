import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { suscripcionesService, type MiSuscripcion } from '@/services';

interface SuscripcionState {
  suscripcion: MiSuscripcion | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setSuscripcion: (suscripcion: MiSuscripcion | null) => void;
  loadSuscripcion: () => Promise<void>;
  cambiarPlan: (planId: number) => Promise<void>;
  clearSuscripcion: () => void;
  
  // Helper methods
  hasFeature: (featureKey: string) => boolean;
  getFeatureUsage: (featureKey: string) => { uso: number; limite: number | null } | null;
  isFeatureLimited: (featureKey: string) => boolean;
  canUseFeature: (featureKey: string) => boolean;
}

export const useSuscripcionStore = create<SuscripcionState>()(
  persist(
    (set, get) => ({
      suscripcion: null,
      isLoading: false,
      error: null,

      setSuscripcion: (suscripcion) => set({ suscripcion, error: null }),

      loadSuscripcion: async () => {
        set({ isLoading: true, error: null });
        try {
          const data = await suscripcionesService.getMiSuscripcion();
          set({ suscripcion: data, isLoading: false, error: null });
        } catch (error) {
          console.error('Error al cargar suscripción:', error);
          set({ 
            suscripcion: null, 
            isLoading: false, 
            error: 'No se pudo cargar la suscripción' 
          });
        }
      },

      cambiarPlan: async (planId: number) => {
        set({ isLoading: true, error: null });
        try {
          const data = await suscripcionesService.cambiarPlan(planId);
          set({ suscripcion: data, isLoading: false, error: null });
        } catch (error) {
          console.error('Error al cambiar plan:', error);
          set({ 
            isLoading: false, 
            error: 'No se pudo cambiar el plan' 
          });
          throw error;
        }
      },

      clearSuscripcion: () => set({ suscripcion: null, error: null }),

      // Helper: Verificar si el usuario tiene acceso a una característica
      hasFeature: (featureKey: string) => {
        const { suscripcion } = get();
        if (!suscripcion) return false;
        
        const feature = suscripcion.features_status.find(
          (f) => f.caracteristica === featureKey
        );
        
        // Si no tiene límite o el límite es null, tiene acceso ilimitado
        if (!feature) return false;
        if (feature.limite_actual === null) return true;
        
        // Si tiene límite, verificar que no lo haya alcanzado
        return feature.uso_actual < feature.limite_actual;
      },

      // Helper: Obtener el uso actual de una característica
      getFeatureUsage: (featureKey: string) => {
        const { suscripcion } = get();
        if (!suscripcion) return null;
        
        const feature = suscripcion.features_status.find(
          (f) => f.caracteristica === featureKey
        );
        
        if (!feature) return null;
        
        return {
          uso: feature.uso_actual,
          limite: feature.limite_actual,
        };
      },

      // Helper: Verificar si una característica tiene límite
      isFeatureLimited: (featureKey: string) => {
        const { suscripcion } = get();
        if (!suscripcion) return true;
        
        const feature = suscripcion.features_status.find(
          (f) => f.caracteristica === featureKey
        );
        
        return feature ? feature.limite_actual !== null : true;
      },

      // Helper: Verificar si puede usar una característica (combinación de hasFeature)
      canUseFeature: (featureKey: string) => {
        const { suscripcion } = get();
        if (!suscripcion) return false;
        
        const feature = suscripcion.features_status.find(
          (f) => f.caracteristica === featureKey
        );
        
        if (!feature) return false;
        
        // Si el límite es 0, no tiene acceso (característica Pro)
        if (feature.limite_actual === 0) return false;
        
        // Si no tiene límite, tiene acceso ilimitado
        if (feature.limite_actual === null) return true;
        
        // Si tiene límite, verificar que no lo haya alcanzado
        return feature.uso_actual < feature.limite_actual;
      },
    }),
    {
      name: 'suscripcion-storage',
      partialize: (state) => ({ 
        suscripcion: state.suscripcion,
      }),
    }
  )
);
