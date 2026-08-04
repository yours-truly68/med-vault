"use client";

import { useMutation } from "@tanstack/react-query";

import { askChat } from "@/lib/api/chat";
import type { ChatAskRequest } from "@/types/api";
import { useAuthStore } from "@/stores/auth-store";

export function useAskChat() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useMutation({
    mutationFn: (payload: ChatAskRequest) => askChat(accessToken, payload),
  });
}
