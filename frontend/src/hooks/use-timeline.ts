"use client";

import { useQuery } from "@tanstack/react-query";

import { listTimelineEvents, type ListTimelineParams } from "@/lib/api/timeline";
import { queryKeys } from "@/lib/query-keys";
import { useAuthStore } from "@/stores/auth-store";

export function useTimelineEvents(params?: ListTimelineParams) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: [...queryKeys.timeline.all, params] as const,
    queryFn: () => listTimelineEvents(accessToken || useAuthStore.getState().accessToken, params),
    enabled: Boolean(accessToken) || isAuthenticated,
  });
}
