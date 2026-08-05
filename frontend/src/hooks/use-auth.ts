"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import {
  getMe,
  login,
  logout,
  refreshSession,
  register,
  type LoginPayload,
  type RegisterPayload,
} from "@/lib/api/auth";
import { ApiError } from "@/lib/api/errors";
import { queryKeys } from "@/lib/query-keys";
import { useAuthStore } from "@/stores/auth-store";

export function useCurrentUser() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: async () => {
      const activeToken = accessToken || useAuthStore.getState().accessToken;
      try {
        const session = await getMe(activeToken);
        return session.user;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          const refreshed = await refreshSession();
          useAuthStore
            .getState()
            .setSession(refreshed.user, refreshed.access_token);
          const session = await getMe(refreshed.access_token);
          return session.user;
        }
        throw error;
      }
    },
    enabled: Boolean(accessToken) || isAuthenticated,
    retry: false,
  });
}

export function useLogin() {
  const setSession = useAuthStore((state) => state.setSession);
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: LoginPayload) => login(payload),
    onSuccess: (data) => {
      setSession(data.user, data.access_token);
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me });
      router.push("/dashboard");
    },
  });
}

export function useRegister() {
  const setSession = useAuthStore((state) => state.setSession);
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (payload: RegisterPayload) => register(payload),
    onSuccess: (data) => {
      setSession(data.user, data.access_token);
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me });
      router.push("/dashboard");
    },
  });
}

export function useLogout() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const clearSession = useAuthStore((state) => state.clearSession);
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: async () => {
      try {
        await logout(accessToken);
      } catch {
        // Clear local session even if logout request fails.
      }
    },
    onSettled: () => {
      clearSession();
      queryClient.clear();
      router.push("/login");
    },
  });
}
