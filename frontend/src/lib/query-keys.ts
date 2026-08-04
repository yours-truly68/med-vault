export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  familyMembers: {
    all: ["family-members"] as const,
    detail: (id: string) => ["family-members", id] as const,
  },
  documents: {
    all: ["documents"] as const,
    detail: (id: string) => ["documents", id] as const,
  },
  search: {
    query: (params: string) => ["search", params] as const,
  },
} as const;
