import { apiClient } from "@/lib/api/client";
import type { HealthTrendsResponse } from "@/types/api";

export type HealthTrendsParams = {
  test_name?: string | null;
  from_date?: string | null;
  to_date?: string | null;
};

export function getHealthTrends(
  token: string | null,
  familyMemberId: string,
  params?: HealthTrendsParams,
) {
  const search = new URLSearchParams();
  if (params?.test_name) search.set("test_name", params.test_name);
  if (params?.from_date) search.set("from_date", params.from_date);
  if (params?.to_date) search.set("to_date", params.to_date);
  const query = search.toString();
  return apiClient<HealthTrendsResponse>(
    `/family-members/${familyMemberId}/health-trends${query ? `?${query}` : ""}`,
    { token },
  );
}
