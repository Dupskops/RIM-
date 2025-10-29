import { create } from "zustand";
import type { Moto } from "@/types";

interface MotoState {
    motos: Moto[];
    selectedMoto: Moto | null;
    isLoading: boolean;

    // Actions
    setMotos: (motos: Moto[]) => void;
    setSelectedMoto: (moto: Moto | null) => void;
    addMoto: (moto: Moto) => void;
    updateMoto: (moto: Moto) => void;
    removeMoto: (motoId: number) => void;
}

export const useMotoStore = create<MotoState>((set) => ({
    motos: [],
    selectedMoto: null,
    isLoading: false,

    setMotos: (motos) => set({ motos }),

    setSelectedMoto: (moto) => set({ selectedMoto: moto }),

    addMoto: (moto) => set((state) => ({ motos: [...state.motos, moto] })),

    updateMoto: (moto) =>
        set((state) => ({
            motos: state.motos.map((m) => (m.id === moto.id ? moto : m)),
            selectedMoto:
                state.selectedMoto?.id === moto.id ? moto : state.selectedMoto,
        })),

    removeMoto: (motoId) =>
        set((state) => ({
            motos: state.motos.filter((m) => m.id !== motoId),
            selectedMoto:
                state.selectedMoto?.id === motoId ? null : state.selectedMoto,
        })),
}));
