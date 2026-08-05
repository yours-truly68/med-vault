"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { CalendarDays, FileText, Search } from "lucide-react";

import { FamilyMemberFilter } from "@/components/documents/family-member-filter";
import { EmptyState, ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { formatDate } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";
import type { Document } from "@/types/api";

import { TimelineRow } from "./timeline-row";
import { TimelineFilters, type TimelineFilterCategory } from "./timeline-filters";

function getTimelineDate(document: Document): string {
  return (
    document.document_date ??
    document.metadata?.document_date ??
    document.created_at.slice(0, 10)
  );
}

function matchesTimelineSearch(
  document: Document,
  query: string,
  filterCategory: TimelineFilterCategory
): boolean {
  // Category & Filter logic
  if (filterCategory !== "all") {
    if (filterCategory === "recent") {
      const docDate = new Date(getTimelineDate(document));
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 365);
      if (docDate < thirtyDaysAgo) return false;
    } else if (filterCategory === "abnormal") {
      const labs = document.metadata?.lab_measurements || [];
      const hasAbnormal = labs.some((lab) => {
        const numVal = typeof lab.value === "number" ? lab.value : parseFloat(String(lab.value));
        const refLow = typeof lab.reference_low === "number" ? lab.reference_low : parseFloat(String(lab.reference_low));
        const refHigh = typeof lab.reference_high === "number" ? lab.reference_high : parseFloat(String(lab.reference_high));
        return (!isNaN(numVal) && !isNaN(refHigh) && numVal > refHigh) || (!isNaN(numVal) && !isNaN(refLow) && numVal < refLow);
      });
      if (!hasAbnormal) return false;
    } else if (filterCategory === "completed") {
      if (document.status !== "completed") return false;
    } else if (document.document_type !== filterCategory) {
      return false;
    }
  }

  const q = query.trim().toLowerCase();
  if (!q) return true;

  // Search across: Patient name, Doctor, Hospital, Diagnosis, Medication, Document title, Document type, Lab test, Year, Month, Date, Tags, Abnormal values
  const rawDate = getTimelineDate(document);
  const formattedDate = formatDate(rawDate).toLowerCase();

  const labNames = (document.metadata?.lab_measurements || []).map((l) => l.test_name).join(" ").toLowerCase();
  const medicineNames = (document.metadata?.medicines || []).join(" ").toLowerCase();

  const haystack = [
    rawDate,
    formattedDate,
    document.original_filename,
    document.document_type,
    document.summary?.short_summary,
    document.summary?.key_findings?.join(" "),
    document.metadata?.patient_name,
    document.metadata?.doctor_name,
    document.metadata?.hospital_name,
    document.metadata?.diagnosis,
    labNames,
    medicineNames,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return haystack.includes(q);
}

function groupDocumentsByMonth(documents: Document[]): Map<string, Document[]> {
  const groups = new Map<string, Document[]>();

  for (const document of documents) {
    const date = new Date(getTimelineDate(document));
    const key = Number.isNaN(date.getTime())
      ? "Unknown Date"
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
        new Date(getTimelineDate(a)).getTime()
    );
    groups.set(key, items);
  }

  return groups;
}

export function TimelinePageContent() {
  const documentsQuery = useDocuments();
  const familyMembersQuery = useFamilyMembers();
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<TimelineFilterCategory>("all");

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
          : true
      )
      .filter((doc) => matchesTimelineSearch(doc, searchQuery, activeFilter))
      .sort(
        (a, b) =>
          new Date(getTimelineDate(b)).getTime() -
          new Date(getTimelineDate(a)).getTime()
      );
  }, [documentsQuery.data?.items, selectedFamilyMemberId, searchQuery, activeFilter]);

  const groupedDocuments = useMemo(
    () => groupDocumentsByMonth(filteredDocuments),
    [filteredDocuments]
  );

  if (documentsQuery.isLoading || familyMembersQuery.isLoading) {
    return (
      <>
        <PageHeader
          title="Longitudinal Medical History"
          description="Chronological clinical journey across all reports, visits, and lab panels."
        />
        <LoadingGrid count={4} />
      </>
    );
  }

  if (documentsQuery.isError) {
    return (
      <>
        <PageHeader title="Longitudinal Medical History" />
        <ErrorState
          message="We couldn't load your medical timeline."
          onRetry={() => {
            void documentsQuery.refetch();
          }}
        />
      </>
    );
  }

  const totalDocuments = documentsQuery.data?.total ?? 0;
  const hasActiveFilter = searchQuery.trim().length > 0 || activeFilter !== "all";

  return (
    <div className="space-y-4">
      <PageHeader
        className="mb-0 border-b-0 pb-0"
        title="Longitudinal Medical History"
        description="Patient history timeline — clinical diagnoses, lab panels, and medical events in chronological order."
        actions={<FamilyMemberFilter className="w-full sm:w-56" />}
      />

      {totalDocuments === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="Your medical history timeline is empty"
          description="As you upload medical reports, MedVault extracts clinical diagnoses, doctors, hospitals, and lab panels into your personal medical journey."
          action={
            <Button asChild>
              <Link href="/upload">Upload documents</Link>
            </Button>
          }
        />
      ) : (
        <div className="mx-auto max-w-5xl space-y-4">
          {/* Universal Search & Filter Chips Bar */}
          <TimelineFilters
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            totalCount={filteredDocuments.length}
          />

          {filteredDocuments.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No matching events found"
              description={
                hasActiveFilter
                  ? `No clinical records match your current query or category filter.`
                  : "No events available."
              }
              action={
                hasActiveFilter ? (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchQuery("");
                      setActiveFilter("all");
                    }}
                  >
                    Reset timeline filters
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="space-y-6">
              {Array.from(groupedDocuments.entries()).map(([month, documents]) => (
                <section key={month} className="space-y-1">
                  {/* Pinned Sticky Month Header */}
                  <div className="sticky top-0 z-10 flex items-center justify-between bg-background/95 py-2.5 px-3 backdrop-blur-md border-b border-border/40 shadow-xs">
                    <div className="flex items-center gap-2">
                      <span className="size-2.5 rounded-full bg-brand-accent animate-pulse" />
                      <h2 className="font-heading text-xs font-bold uppercase tracking-widest text-foreground">
                        {month}
                      </h2>
                    </div>
                    <span className="text-[0.6875rem] font-bold text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-full">
                      {documents.length} report{documents.length === 1 ? "" : "s"}
                    </span>
                  </div>

                  {/* Compact Scannable Timeline Rows Container */}
                  <div className="divide-y divide-border/50 rounded-2xl border border-border/70 bg-card/80 overflow-hidden shadow-tinted">
                    {documents.map((doc, idx) => (
                      <TimelineRow
                        key={doc.id}
                        document={doc}
                        familyMember={memberMap.get(doc.family_member_id)}
                        index={idx}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
