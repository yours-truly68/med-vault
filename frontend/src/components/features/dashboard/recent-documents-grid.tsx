"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DocumentCard } from "@/components/documents";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { useUiStore } from "@/stores/ui-store";

export function RecentDocumentsGrid() {
  const documentsQuery = useDocuments();
  const familyMembersQuery = useFamilyMembers();
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);

  const isDocsLoading = documentsQuery.isPending && documentsQuery.fetchStatus === "fetching";
  const isFamilyLoading = familyMembersQuery.isPending && familyMembersQuery.fetchStatus === "fetching";

  if ((isDocsLoading || isFamilyLoading) && !documentsQuery.data && !familyMembersQuery.data) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-6 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (documentsQuery.isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive">
        Unable to load recent medical documents.
      </div>
    );
  }

  const documents = documentsQuery.data?.items ?? [];
  const familyMembers = familyMembersQuery.data?.items ?? [];
  const memberMap = new Map(familyMembers.map((member) => [member.id, member]));

  const activeDocs = selectedFamilyMemberId
    ? documents.filter((d) => d.family_member_id === selectedFamilyMemberId)
    : documents;

  const recentDocuments = [...activeDocs]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(0, 3);

  if (recentDocuments.length === 0) return null;

  return (
    <section className="space-y-3.5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-heading text-base font-bold tracking-tight text-foreground">
            Recent Medical Documents
          </h2>
          <p className="text-xs text-muted-foreground">
            Latest uploaded records across your family vault.
          </p>
        </div>
        <Button variant="outline" size="sm" asChild className="rounded-xl text-xs gap-1">
          <Link href="/documents">
            <span>View All Vault Documents</span>
            <ArrowRight className="size-3" />
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {recentDocuments.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            familyMember={memberMap.get(doc.family_member_id)}
            href={`/documents/${doc.id}`}
          />
        ))}
      </div>
    </section>
  );
}
