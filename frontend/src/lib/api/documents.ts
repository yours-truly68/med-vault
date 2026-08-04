import { apiClient } from "@/lib/api/client";
import type {
  Document,
  DocumentListResponse,
  DocumentStatus,
  DocumentType,
  DocumentUploadListResponse,
  MessageResponse,
} from "@/types/api";

export type ListDocumentsParams = {
  family_member_id?: string | null;
  document_type?: DocumentType | null;
  status?: DocumentStatus | null;
};

export function listDocuments(
  token: string | null,
  params?: ListDocumentsParams,
) {
  const search = new URLSearchParams();
  if (params?.family_member_id) {
    search.set("family_member_id", params.family_member_id);
  }
  if (params?.document_type) {
    search.set("document_type", params.document_type);
  }
  if (params?.status) {
    search.set("status", params.status);
  }
  const query = search.toString();
  return apiClient<DocumentListResponse>(
    `/documents${query ? `?${query}` : ""}`,
    { token },
  );
}

export function getDocument(token: string | null, documentId: string) {
  return apiClient<Document>(`/documents/${documentId}`, { token });
}

export function deleteDocument(token: string | null, documentId: string) {
  return apiClient<MessageResponse>(`/documents/${documentId}`, {
    method: "DELETE",
    token,
  });
}

export function reprocessDocument(token: string | null, documentId: string) {
  return apiClient<Document>(`/documents/${documentId}/reprocess`, {
    method: "POST",
    token,
  });
}

export function uploadDocuments(
  token: string | null,
  familyMemberId: string,
  files: File[],
) {
  const formData = new FormData();
  formData.append("family_member_id", familyMemberId);
  for (const file of files) {
    formData.append("files", file);
  }

  return apiClient<DocumentUploadListResponse>("/documents/upload", {
    method: "POST",
    token,
    body: formData,
  });
}
