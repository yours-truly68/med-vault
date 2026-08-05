"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createFamilyMember,
  deleteFamilyMember,
  listFamilyMembers,
  updateFamilyMember,
} from "@/lib/api/family-members";
import { queryKeys } from "@/lib/query-keys";
import type { FamilyMemberCreate, FamilyMemberUpdate } from "@/types/api";
import { useAuthStore } from "@/stores/auth-store";

export function useFamilyMembers() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    queryKey: queryKeys.familyMembers.all,
    queryFn: () => listFamilyMembers(accessToken || useAuthStore.getState().accessToken),
    enabled: Boolean(accessToken) || isAuthenticated,
  });
}

export function useCreateFamilyMember() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: FamilyMemberCreate) =>
      createFamilyMember(accessToken, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyMembers.all });
    },
  });
}

export function useUpdateFamilyMember() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: FamilyMemberUpdate;
    }) => updateFamilyMember(accessToken, id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyMembers.all });
    },
  });
}

export function useDeleteFamilyMember() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteFamilyMember(accessToken, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.familyMembers.all });
    },
  });
}
