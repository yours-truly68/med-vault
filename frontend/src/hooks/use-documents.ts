"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  getDocument,
  listDocuments,
  reprocessDocument,
  uploadDocuments,
  type ListDocumentsParams,
} from "@/lib/api/documents";
import { queryKeys } from "@/lib/query-keys";
import { useAuthStore } from "@/stores/auth-store";

type UseDocumentsOptions = ListDocumentsParams & {
  /** Poll while any document is pending/processing so upload status stays live. */
  pollWhileProcessing?: boolean;
};

export function useDocuments(options?: UseDocumentsOptions) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { pollWhileProcessing, ...filters } = options ?? {};

  return useQuery({
    queryKey: [...queryKeys.documents.all, filters] as const,
    queryFn: () => listDocuments(accessToken, filters),
    enabled: hasHydrated && isAuthenticated,
    refetchInterval: (query) => {
      if (!pollWhileProcessing) return false;
      const items = query.state.data?.items ?? [];
      const busy = items.some(
        (doc) => doc.status === "pending" || doc.status === "processing",
      );
      return busy ? 3000 : false;
    },
  });
}

export function useDocument(documentId: string) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: queryKeys.documents.detail(documentId),
    queryFn: () => getDocument(accessToken, documentId),
    enabled: hasHydrated && isAuthenticated && Boolean(documentId),
    refetchInterval: (query) => {
      const doc = query.state.data;
      if (!doc) return false;
      if (doc.status === "pending" || doc.status === "processing") {
        return 3000;
      }
      return false;
    },
  });
}

export function useUploadDocuments() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      familyMemberId,
      files,
    }: {
      familyMemberId: string;
      files: File[];
    }) => uploadDocuments(accessToken, familyMemberId, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
  });
}

export function useDeleteDocument() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => deleteDocument(accessToken, documentId),
    onSuccess: (_data, documentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      queryClient.removeQueries({
        queryKey: queryKeys.documents.detail(documentId),
      });
    },
  });
}

export function useReprocessDocument() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) =>
      reprocessDocument(accessToken, documentId),
    onSuccess: (_data, documentId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.detail(documentId),
      });
    },
  });
}
