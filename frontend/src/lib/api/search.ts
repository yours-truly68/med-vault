import { apiClient } from "@/lib/api/client";
import type { SearchRequest, SearchResponse } from "@/types/api";

export function searchDocuments(token: string | null, payload: SearchRequest) {
  return apiClient<SearchResponse>("/search", {
    method: "POST",
    token,
    body: payload,
  });
}
