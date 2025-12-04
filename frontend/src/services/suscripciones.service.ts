import apiClient from '@/config/api-client';
import { API_ENDPOINTS } from '@/config/api-endpoints';

/**
 * Tipos para Planes de Suscripción
 */
export interface Caracteristica {
  id: number;
  clave_funcion: string;
  descripcion: string;
  limite_free: number | null;
  limite_pro: number | null;
}

export interface Plan {
  id: number;
  nombre_plan: string;
  precio: string;
  periodo_facturacion: string;
  caracteristicas: Caracteristica[];
}

export interface PlanesResponse {
  success: boolean;
  message: string;
  data: Plan[];
  timestamp: string;
  version: string;
}

/**
 * Tipos para Mi Suscripción
 */
export interface FeatureStatus {
  caracteristica: string;
  descripcion: string;
  uso_actual: number;
  limite_actual: number | null;
  limite_pro: number | null;
  upsell_message: string | null;
}

export interface MiSuscripcion {
  id: number;
  usuario_id: number;
  plan: Plan;
  fecha_inicio: string;
  fecha_fin: string | null;
  estado_suscripcion: string;
  features_status: FeatureStatus[];
}

export interface MiSuscripcionResponse {
  success: boolean;
  message: string;
  data: MiSuscripcion;
  timestamp: string;
  version: string;
}

/**
 * Servicio para gestionar suscripciones
 */
export const suscripcionesService = {
  /**
   * Obtener todos los planes disponibles
   */
  async getPlanes(): Promise<Plan[]> {
    const resp = await apiClient.get<PlanesResponse>(API_ENDPOINTS.SUSCRIPCIONES.PLANES);
    return resp.data?.data ?? [];
  },

  /**
   * Obtener la suscripción activa del usuario con detalles de uso
   */
  async getMiSuscripcion(): Promise<MiSuscripcion> {
    const resp = await apiClient.get<MiSuscripcionResponse>(API_ENDPOINTS.SUSCRIPCIONES.MI_SUSCRIPCION);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Cambiar plan de suscripción
   */
  async cambiarPlan(planId: number): Promise<MiSuscripcion> {
    const resp = await apiClient.post<MiSuscripcionResponse>(
      API_ENDPOINTS.SUSCRIPCIONES.CAMBIAR_PLAN, 
      { plan_id: planId }
    );
    return resp.data?.data ?? resp.data;
  },

  /**
   * Obtener la suscripción actual del usuario
   */
  async getMySuscripcion(): Promise<any> {
    const resp = await apiClient.get(API_ENDPOINTS.SUSCRIPCIONES.ME);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Actualizar/Mejorar plan de suscripción
   */
  async upgradePlan(planId: number): Promise<any> {
    const resp = await apiClient.post(API_ENDPOINTS.SUSCRIPCIONES.UPGRADE, { plan_id: planId });
    return resp.data?.data ?? resp.data;
  },

  /**
   * Cancelar suscripción
   */
  async cancelSuscripcion(): Promise<any> {
    const resp = await apiClient.post(API_ENDPOINTS.SUSCRIPCIONES.CANCEL);
    return resp.data?.data ?? resp.data;
  },

  /**
   * Renovar suscripción
   */
  async renewSuscripcion(): Promise<any> {
    const resp = await apiClient.post(API_ENDPOINTS.SUSCRIPCIONES.RENEW);
    return resp.data?.data ?? resp.data;
  },
};
