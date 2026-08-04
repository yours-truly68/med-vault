"use client";

import { useMutation } from "@tanstack/react-query";

import { searchDocuments } from "@/lib/api/search";
import type { SearchRequest } from "@/types/api";
import { useAuthStore } from "@/stores/auth-store";

export function useSearchDocuments() {
  const accessToken = useAuthStore((state) => state.accessToken);

  return useMutation({
    mutationFn: (payload: SearchRequest) =>
      searchDocuments(accessToken, payload),
  });
}
