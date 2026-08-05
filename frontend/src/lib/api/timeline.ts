import { apiClient } from "@/lib/api/client";
import type { TimelineListResponse } from "@/types/api";

export type ListTimelineParams = {
  family_member_id?: string | null;
  from_date?: string | null;
  to_date?: string | null;
  event_type?: string | null;
  limit?: number;
  offset?: number;
};

export function listTimelineEvents(
  token: string | null,
  params?: ListTimelineParams,
) {
  const search = new URLSearchParams();
  if (params?.family_member_id) {
    search.set("family_member_id", params.family_member_id);
  }
  if (params?.from_date) search.set("from_date", params.from_date);
  if (params?.to_date) search.set("to_date", params.to_date);
  if (params?.event_type) search.set("event_type", params.event_type);
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.offset) search.set("offset", String(params.offset));
  const query = search.toString();
  return apiClient<TimelineListResponse>(`/timeline${query ? `?${query}` : ""}`, {
    token,
  });
}
