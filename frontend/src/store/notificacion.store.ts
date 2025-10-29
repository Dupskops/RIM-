import { create } from "zustand";
import type { Notificacion } from "@/types";

interface NotificacionState {
    notificaciones: Notificacion[];
    sinLeer: number;

    // Actions
    setNotificaciones: (notificaciones: Notificacion[]) => void;
    addNotificacion: (notificacion: Notificacion) => void;
    marcarLeida: (notificacionId: number) => void;
    marcarTodasLeidas: () => void;
    eliminarNotificacion: (notificacionId: number) => void;
}

export const useNotificacionStore = create<NotificacionState>((set) => ({
    notificaciones: [],
    sinLeer: 0,

    setNotificaciones: (notificaciones) =>
        set({
            notificaciones,
            sinLeer: notificaciones.filter((n) => !n.leida).length,
        }),

    addNotificacion: (notificacion) =>
        set((state) => ({
            notificaciones: [notificacion, ...state.notificaciones],
            sinLeer: !notificacion.leida ? state.sinLeer + 1 : state.sinLeer,
        })),

    marcarLeida: (notificacionId) =>
        set((state) => {
            const notificaciones = state.notificaciones.map((n) =>
                n.id === notificacionId ? { ...n, leida: true } : n
            );
            return {
                notificaciones,
                sinLeer: notificaciones.filter((n) => !n.leida).length,
            };
        }),

    marcarTodasLeidas: () =>
        set((state) => ({
            notificaciones: state.notificaciones.map((n) => ({
                ...n,
                leida: true,
            })),
            sinLeer: 0,
        })),

    eliminarNotificacion: (notificacionId) =>
        set((state) => {
            const notificaciones = state.notificaciones.filter(
                (n) => n.id !== notificacionId
            );
            return {
                notificaciones,
                sinLeer: notificaciones.filter((n) => !n.leida).length,
            };
        }),
}));
