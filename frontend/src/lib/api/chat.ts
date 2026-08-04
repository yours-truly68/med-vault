import { apiClient } from "@/lib/api/client";
import type { ChatAskRequest, ChatAskResponse } from "@/types/api";

export function askChat(token: string | null, payload: ChatAskRequest) {
  return apiClient<ChatAskResponse>("/chat/ask", {
    method: "POST",
    token,
    body: payload,
  });
}
