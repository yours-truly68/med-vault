"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { FileText, Search } from "lucide-react";

import {
  DocumentCard,
  DocumentTypeFilter,
  FamilyMemberFilter,
} from "@/components/documents";
import { EmptyState, ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { useSearchDocuments } from "@/hooks/use-search";
import { useUiStore } from "@/stores/ui-store";
import type { Document, DocumentType } from "@/types/api";

function filterDocuments(
  documents: Document[],
  familyMemberId: string | null,
  documentType: DocumentType | null,
  searchQuery: string,
): Document[] {
  let filtered = documents;

  if (familyMemberId) {
    filtered = filtered.filter((doc) => doc.family_member_id === familyMemberId);
  }

  if (documentType) {
    filtered = filtered.filter((doc) => doc.document_type === documentType);
  }

  if (searchQuery.trim()) {
    const query = searchQuery.trim().toLowerCase();
    filtered = filtered.filter((doc) => {
      const haystack = [
        doc.original_filename,
        doc.summary?.short_summary,
        doc.metadata?.patient_name,
        doc.metadata?.doctor_name,
        doc.metadata?.hospital_name,
        doc.metadata?.diagnosis,
        doc.document_type,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(query);
    });
  }

  return filtered.sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
}

export function DocumentsPageContent() {
  const documentsQuery = useDocuments({ pollWhileProcessing: true });
  const familyMembersQuery = useFamilyMembers();
  const searchMutation = useSearchDocuments();
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId,
  );
  const [localQuery, setLocalQuery] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType | null>(null);

  const memberMap = useMemo(() => {
    const members = familyMembersQuery.data?.items ?? [];
    return new Map(members.map((member) => [member.id, member]));
  }, [familyMembersQuery.data?.items]);

  const filteredDocuments = useMemo(() => {
    if (!documentsQuery.data?.items) return [];
    return filterDocuments(
      documentsQuery.data.items,
      selectedFamilyMemberId,
      documentType,
      localQuery,
    );
  }, [
    documentsQuery.data?.items,
    selectedFamilyMemberId,
    documentType,
    localQuery,
  ]);

  const rejectedCount = useMemo(
    () =>
      (documentsQuery.data?.items ?? []).filter(
        (doc) => doc.status === "rejected",
      ).length,
    [documentsQuery.data?.items],
  );

  if (documentsQuery.isLoading || familyMembersQuery.isLoading) {
    return (
      <>
        <PageHeader
          title="Documents"
          description="Browse and search your family's medical records."
        />
        <LoadingGrid />
      </>
    );
  }

  if (documentsQuery.isError) {
    return (
      <>
        <PageHeader title="Documents" />
        <ErrorState
          message="We couldn't load your documents."
          onRetry={() => void documentsQuery.refetch()}
        />
      </>
    );
  }

  const allDocuments = documentsQuery.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Documents"
        description="Browse and search your family's medical records."
        actions={
          <Button asChild>
            <Link href="/upload">Upload</Link>
          </Button>
        }
      />

      {rejectedCount > 0 ? (
        <div
          role="status"
          className="mb-5 rounded-lg border border-orange-500/30 bg-orange-500/8 px-4 py-3 text-sm text-orange-900 dark:text-orange-200"
        >
          {rejectedCount} upload
          {rejectedCount === 1 ? " was" : "s were"} rejected as non-medical and
          never indexed. Open each file and delete it to keep your vault clean.
        </div>
      ) : null}

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative min-w-[12rem] flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={localQuery}
            onChange={(event) => setLocalQuery(event.target.value)}
            placeholder="Filter by filename, doctor, diagnosis..."
            className="pl-9"
          />
        </div>
        <DocumentTypeFilter value={documentType} onChange={setDocumentType} />
        <FamilyMemberFilter className="w-full sm:w-56" />
        <Button
          variant="outline"
          disabled={!localQuery.trim() || searchMutation.isPending}
          onClick={() => {
            if (!localQuery.trim()) return;
            void searchMutation.mutate({
              query: localQuery.trim(),
              family_member_id: selectedFamilyMemberId,
            });
          }}
        >
          {searchMutation.isPending ? "Searching..." : "Semantic search"}
        </Button>
      </div>

      {searchMutation.data && searchMutation.data.total > 0 ? (
        <section className="mb-8 space-y-3">
          <h2 className="text-sm font-medium text-muted-foreground">
            Semantic matches for &ldquo;{searchMutation.data.query}&rdquo;
          </h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {searchMutation.data.results.map((result) => {
              const document = allDocuments.find(
                (item) => item.id === result.document_id,
              );
              if (!document) return null;
              return (
                <DocumentCard
                  key={result.document_id}
                  document={document}
                  familyMember={memberMap.get(document.family_member_id)}
                  href={`/documents/${document.id}`}
                />
              );
            })}
          </div>
        </section>
      ) : null}

      {allDocuments.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Your vault is empty"
          description="Upload prescriptions, labs, bills, or imaging reports. MedVault will extract text, classify them, and write a summary you can search later."
          action={
            <Button asChild>
              <Link href="/upload">Upload your first document</Link>
            </Button>
          }
          secondaryAction={
            <Button asChild variant="outline">
              <Link href="/family-members">Manage family</Link>
            </Button>
          }
        />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No matches for these filters"
          description="Clear the type filter, switch family member, or try a shorter search phrase."
          action={
            <Button
              variant="outline"
              onClick={() => {
                setLocalQuery("");
                setDocumentType(null);
              }}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
          {filteredDocuments.map((document) => (
            <DocumentCard
              key={document.id}
              document={document}
              familyMember={memberMap.get(document.family_member_id)}
              href={`/documents/${document.id}`}
            />
          ))}
        </div>
      )}
    </>
  );
}
