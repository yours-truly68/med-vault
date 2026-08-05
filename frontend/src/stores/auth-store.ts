import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
};

type AuthState = {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  setSession: (user: AuthUser, accessToken: string) => void;
  setAccessToken: (accessToken: string | null) => void;
  clearSession: () => void;
  setHasHydrated: (value: boolean) => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      hasHydrated: false,
      setSession: (user, accessToken) =>
        set({ user, accessToken, isAuthenticated: true, hasHydrated: true }),
      setAccessToken: (accessToken) =>
        set({
          accessToken,
          isAuthenticated: Boolean(accessToken),
          hasHydrated: true,
        }),
      clearSession: () =>
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          hasHydrated: true,
        }),
      setHasHydrated: (value) => set({ hasHydrated: value }),
    }),
    {
      name: "medvault-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);

export function getAccessToken(): string | null {
  return useAuthStore.getState().accessToken;
}
