"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ChatAskResponse } from "@/types/api";

export type CopilotMode = "minimized" | "expanded" | "docked" | "fullscreen";

export type DockCorner =
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right";

export type ChatLifecycleState =
  | "IDLE"
  | "CONNECTING"
  | "STREAMING"
  | "FINISHED"
  | "FAILED"
  | "CANCELLED";

export type ThinkingStage =
  | "searching"
  | "retrieving"
  | "selecting"
  | "synthesizing"
  | null;

export type CopilotMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatAskResponse;
  pageContext?: string;
  error?: string;
  timestamp: number;
};

type CopilotStore = {
  isOpen: boolean;
  mode: CopilotMode;
  dockCorner: DockCorner;
  messages: CopilotMessage[];
  isFirstLaunch: boolean;
  chatState: ChatLifecycleState;
  thinkingStage: ThinkingStage;

  // Actions
  setIsOpen: (isOpen: boolean) => void;
  toggleCopilot: () => void;
  setMode: (mode: CopilotMode) => void;
  setDockCorner: (corner: DockCorner) => void;
  setChatState: (state: ChatLifecycleState) => void;
  setThinkingStage: (stage: ThinkingStage) => void;
  addMessage: (message: Omit<CopilotMessage, "timestamp">) => void;
  updateMessage: (id: string, update: Partial<CopilotMessage>) => void;
  clearMessages: () => void;
  completeOnboarding: () => void;
};

export const useCopilotStore = create<CopilotStore>()(
  persist(
    (set) => ({
      isOpen: false,
      mode: "expanded",
      dockCorner: "bottom-right",
      messages: [],
      isFirstLaunch: true,
      chatState: "IDLE",
      thinkingStage: null,

      setIsOpen: (isOpen) => set({ isOpen }),

      toggleCopilot: () =>
        set((state) => ({
          isOpen: !state.isOpen,
          mode: !state.isOpen && state.mode === "minimized" ? "expanded" : state.mode,
        })),

      setMode: (mode) =>
        set({
          mode,
          isOpen: mode !== "minimized",
        }),

      setDockCorner: (dockCorner) => set({ dockCorner }),
      setChatState: (chatState) => set({ chatState }),
      setThinkingStage: (thinkingStage) => set({ thinkingStage }),

      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            { ...message, timestamp: Date.now() },
          ],
        })),

      updateMessage: (id, update) =>
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === id ? { ...msg, ...update } : msg
          ),
        })),

      clearMessages: () => set({ messages: [], chatState: "IDLE", thinkingStage: null }),

      completeOnboarding: () => set({ isFirstLaunch: false }),
    }),
    {
      name: "medvault-copilot-storage-v3",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        messages: state.messages,
        mode: state.mode,
        dockCorner: state.dockCorner,
        isFirstLaunch: state.isFirstLaunch,
      }),
    }
  )
);
