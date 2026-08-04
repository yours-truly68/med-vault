"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { CalendarDays, FileText, Search } from "lucide-react";

import { DocumentTypeBadge } from "@/components/documents";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { FamilyMemberFilter } from "@/components/documents/family-member-filter";
import { EmptyState, ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { formatDate } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";
import type { Document } from "@/types/api";

function getTimelineDate(document: Document): string {
  return (
    document.document_date ??
    document.metadata?.document_date ??
    document.created_at.slice(0, 10)
  );
}

function dateSearchTokens(document: Document): string[] {
  const raw = getTimelineDate(document);
  const date = new Date(raw.includes("T") ? raw : `${raw}T00:00:00`);
  if (Number.isNaN(date.getTime())) return ["unknown"];

  const monthLong = new Intl.DateTimeFormat("en-US", { month: "long" }).format(
    date,
  );
  const monthShort = new Intl.DateTimeFormat("en-US", { month: "short" }).format(
    date,
  );
  const year = String(date.getFullYear());
  const day = String(date.getDate());
  const dayPad = day.padStart(2, "0");
  const monthNum = String(date.getMonth() + 1).padStart(2, "0");
  const iso = `${year}-${monthNum}-${dayPad}`;

  return [
    monthLong,
    monthShort,
    year,
    day,
    dayPad,
    monthNum,
    iso,
    `${monthLong} ${year}`,
    `${monthShort} ${year}`,
    `${monthLong} ${day}`,
    `${monthShort} ${day}`,
    `${monthNum}/${dayPad}/${year}`,
    `${dayPad}/${monthNum}/${year}`,
    formatDate(raw),
  ].map((token) => token.toLowerCase());
}

function matchesTimelineSearch(document: Document, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;

  const nameHaystack = [
    document.original_filename,
    document.summary?.short_summary,
    document.metadata?.patient_name,
    document.metadata?.doctor_name,
    document.metadata?.hospital_name,
    document.metadata?.diagnosis,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (nameHaystack.includes(q)) return true;

  const tokens = dateSearchTokens(document);
  if (tokens.some((token) => token.includes(q) || q.includes(token))) {
    // Prefer meaningful length so single-digit days don't over-match everything
    if (q.length >= 3) return true;
    if (tokens.includes(q)) return true;
  }

  // Month-only or year-only (e.g. "march", "2024")
  const monthOrYear = tokens.slice(0, 3);
  if (monthOrYear.some((token) => token === q || token.startsWith(q))) {
    return true;
  }

  return false;
}

function groupDocumentsByMonth(documents: Document[]): Map<string, Document[]> {
  const groups = new Map<string, Document[]>();

  for (const document of documents) {
    const date = new Date(getTimelineDate(document));
    const key = Number.isNaN(date.getTime())
      ? "Unknown"
      : new Intl.DateTimeFormat("en-US", {
          month: "long",
          year: "numeric",
        }).format(date);

    const existing = groups.get(key) ?? [];
    existing.push(document);
    groups.set(key, existing);
  }

  for (const [key, items] of groups) {
    items.sort(
      (a, b) =>
        new Date(getTimelineDate(b)).getTime() -
        new Date(getTimelineDate(a)).getTime(),
    );
    groups.set(key, items);
  }

  return groups;
}

export function TimelinePageContent() {
  const documentsQuery = useDocuments();
  const familyMembersQuery = useFamilyMembers();
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId,
  );
  const [searchQuery, setSearchQuery] = useState("");

  const memberMap = useMemo(() => {
    const members = familyMembersQuery.data?.items ?? [];
    return new Map(members.map((member) => [member.id, member]));
  }, [familyMembersQuery.data?.items]);

  const filteredDocuments = useMemo(() => {
    const items = documentsQuery.data?.items ?? [];
    return items
      .filter((doc) =>
        selectedFamilyMemberId
          ? doc.family_member_id === selectedFamilyMemberId
          : true,
      )
      .filter((doc) => matchesTimelineSearch(doc, searchQuery))
      .sort(
        (a, b) =>
          new Date(getTimelineDate(b)).getTime() -
          new Date(getTimelineDate(a)).getTime(),
      );
  }, [
    documentsQuery.data?.items,
    selectedFamilyMemberId,
    searchQuery,
  ]);

  const groupedDocuments = useMemo(
    () => groupDocumentsByMonth(filteredDocuments),
    [filteredDocuments],
  );

  if (documentsQuery.isLoading || familyMembersQuery.isLoading) {
    return (
      <>
        <PageHeader
          title="Timeline"
          description="See your family's medical history in chronological order."
        />
        <LoadingGrid count={3} />
      </>
    );
  }

  if (documentsQuery.isError) {
    return (
      <>
        <PageHeader title="Timeline" />
        <ErrorState
          message="We couldn't load your timeline."
          onRetry={() => void documentsQuery.refetch()}
        />
      </>
    );
  }

  const totalDocuments = documentsQuery.data?.total ?? 0;
  const hasActiveSearch = searchQuery.trim().length > 0;

  return (
    <>
      <PageHeader
        title="Timeline"
        description="See your family's medical history in chronological order."
        actions={<FamilyMemberFilter className="w-full sm:w-56" />}
      />

      {totalDocuments === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Your timeline is empty"
          description="As you upload documents, MedVault will place them along a chronological health timeline."
          action={
            <Button asChild>
              <Link href="/upload">Upload documents</Link>
            </Button>
          }
        />
      ) : (
        <div className="mx-auto max-w-3xl space-y-6">
          <div className="relative">
            <Search
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by document name, month, or date"
              className="pl-9"
              aria-label="Search timeline"
            />
          </div>

          {filteredDocuments.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No matching documents"
              description={
                hasActiveSearch
                  ? `Nothing matched “${searchQuery.trim()}”. Try a filename, a month like March, or a date like 2024-03-15.`
                  : "No documents for this filter."
              }
              action={
                hasActiveSearch ? (
                  <Button variant="outline" onClick={() => setSearchQuery("")}>
                    Clear search
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-8">
              {Array.from(groupedDocuments.entries()).map(([month, documents]) => (
                <section key={month} className="space-y-4">
                  <h2 className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
                    {month}
                  </h2>
                  <div className="relative space-y-4 border-l border-border pl-6">
                    {documents.map((document) => {
                      const member = memberMap.get(document.family_member_id);
                      return (
                        <Card
                          key={document.id}
                          className="interactive-card relative border-border/80 bg-card/80 backdrop-blur-sm"
                        >
                          <span className="absolute top-6 -left-[1.9rem] size-3 rounded-full border-2 border-background bg-primary" />
                          <CardHeader className="space-y-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0 space-y-1">
                                <CardTitle className="text-base">
                                  <Link
                                    href={`/documents/${document.id}`}
                                    className="break-all hover:underline"
                                  >
                                    {document.original_filename}
                                  </Link>
                                </CardTitle>
                                {document.summary?.short_summary ? (
                                  <CardDescription className="line-clamp-2">
                                    {document.summary.short_summary}
                                  </CardDescription>
                                ) : null}
                                <CardDescription>
                                  {member?.name} ·{" "}
                                  {formatDate(getTimelineDate(document))}
                                </CardDescription>
                              </div>
                              <FileText className="size-4 shrink-0 text-muted-foreground" />
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <DocumentTypeBadge type={document.document_type} />
                              <DocumentStatusBadge status={document.status} />
                            </div>
                          </CardHeader>
                          {document.summary?.key_findings.length ? (
                            <CardContent>
                              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                                {document.summary.key_findings
                                  .slice(0, 2)
                                  .map((finding) => (
                                    <li key={finding}>{finding}</li>
                                  ))}
                              </ul>
                            </CardContent>
                          ) : null}
                        </Card>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
