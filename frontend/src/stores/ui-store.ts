import { create } from "zustand";

type LlmBusySource = "processing" | "chat" | "general";

type UiState = {
  isSidebarOpen: boolean;
  selectedFamilyMemberId: string | null;
  llmBusyBannerVisible: boolean;
  llmBusySource: LlmBusySource | null;
  llmBusyDetail: string | null;
  llmBusyToastedKeys: string[];
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSelectedFamilyMemberId: (id: string | null) => void;
  /**
   * Show a one-time toast for this incident key and open the persistent banner.
   * Banner stays until acknowledgeLlmBusy() — even if the underlying job recovers.
   */
  notifyLlmRateLimited: (input: {
    key: string;
    detail?: string | null;
    source?: LlmBusySource;
  }) => void;
  acknowledgeLlmBusy: () => void;
};

export const useUiStore = create<UiState>((set, get) => ({
  isSidebarOpen: false,
  selectedFamilyMemberId: null,
  llmBusyBannerVisible: false,
  llmBusySource: null,
  llmBusyDetail: null,
  llmBusyToastedKeys: [],
  toggleSidebar: () =>
    set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),
  setSelectedFamilyMemberId: (id) => set({ selectedFamilyMemberId: id }),
  notifyLlmRateLimited: ({ key, detail, source = "general" }) => {
    const state = get();
    const alreadyToasted = state.llmBusyToastedKeys.includes(key);

    set({
      llmBusyBannerVisible: true,
      llmBusySource: source,
      llmBusyDetail: detail ?? state.llmBusyDetail,
      llmBusyToastedKeys: alreadyToasted
        ? state.llmBusyToastedKeys
        : [...state.llmBusyToastedKeys, key],
    });

    if (!alreadyToasted) {
      // Lazy import keeps the store free of SSR toast issues.
      void import("sonner").then(({ toast }) => {
        toast.warning("AI rate limit reached", {
          id: `llm-rate-limit-${key}`,
          description:
            "The language model is busy. We'll retry automatically — or try again in a few minutes.",
          duration: 6000,
        });
      });
    }
  },
  acknowledgeLlmBusy: () =>
    set({
      llmBusyBannerVisible: false,
      llmBusySource: null,
      llmBusyDetail: null,
      llmBusyToastedKeys: [],
    }),
}));
