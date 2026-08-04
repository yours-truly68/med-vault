import { apiClient } from "@/lib/api/client";
import type {
  FamilyMember,
  FamilyMemberCreate,
  FamilyMemberListResponse,
  FamilyMemberUpdate,
  MessageResponse,
} from "@/types/api";

export function listFamilyMembers(token: string | null) {
  return apiClient<FamilyMemberListResponse>("/family-members", { token });
}

export function createFamilyMember(
  token: string | null,
  payload: FamilyMemberCreate,
) {
  return apiClient<FamilyMember>("/family-members", {
    method: "POST",
    token,
    body: payload,
  });
}

export function updateFamilyMember(
  token: string | null,
  id: string,
  payload: FamilyMemberUpdate,
) {
  return apiClient<FamilyMember>(`/family-members/${id}`, {
    method: "PATCH",
    token,
    body: payload,
  });
}

export function deleteFamilyMember(token: string | null, id: string) {
  return apiClient<MessageResponse>(`/family-members/${id}`, {
    method: "DELETE",
    token,
  });
}
