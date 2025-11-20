import { create } from "zustand";
import { persist } from "zustand/middleware";

interface NavState {
    activeIndex: number;
    setActiveIndex: (index: number) => void;
}

// Persist activeIndex so it survives page reloads
export const useNavStore = create<NavState>()(
    persist(
        (set) => ({
            activeIndex: 0,
            setActiveIndex: (index: number) => set({ activeIndex: index }),
        }),
        {
            name: "nav-storage", // localStorage key
            partialize: (state) => ({ activeIndex: state.activeIndex }),
        }
    )
);

export default useNavStore;
