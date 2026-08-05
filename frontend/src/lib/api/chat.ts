import { apiClient, type RequestOptions } from "@/lib/api/client";
import type { ChatAskRequest, ChatAskResponse } from "@/types/api";

export function askChat(
  token: string | null,
  payload: ChatAskRequest,
  options?: Omit<RequestOptions, "body" | "token">
) {
  return apiClient<ChatAskResponse>("/chat/ask", {
    method: "POST",
    token,
    body: payload,
    ...options,
  });
}
