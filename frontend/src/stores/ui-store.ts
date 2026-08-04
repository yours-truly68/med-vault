import { create } from "zustand";

type UiState = {
  isSidebarOpen: boolean;
  selectedFamilyMemberId: string | null;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSelectedFamilyMemberId: (id: string | null) => void;
};

export const useUiStore = create<UiState>((set) => ({
  isSidebarOpen: false,
  selectedFamilyMemberId: null,
  toggleSidebar: () =>
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  setSelectedFamilyMemberId: (id) => set({ selectedFamilyMemberId: id }),
}));
