"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealthTrends, type HealthTrendsParams } from "@/lib/api/health";
import { queryKeys } from "@/lib/query-keys";
import { useAuthStore } from "@/stores/auth-store";

export function useHealthTrends(
  familyMemberId: string | null,
  params?: HealthTrendsParams,
) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: [
      ...queryKeys.health.trends(familyMemberId ?? "none"),
      params,
    ] as const,
    queryFn: () => getHealthTrends(accessToken, familyMemberId!, params),
    enabled: hasHydrated && isAuthenticated && Boolean(familyMemberId),
  });
}
