"use client";

import { motion } from "framer-motion";
import { User, AlertTriangle, ShieldCheck, FileText, ChevronRight } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { getUserInitials } from "@/lib/user";
import { formatDate, formatRelationship } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { useDocuments } from "@/hooks/use-documents";
import { cn } from "@/lib/utils";

export function FamilyOverviewGrid() {
  const familyMembersQuery = useFamilyMembers();
  const documentsQuery = useDocuments();
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);
  const setSelectedFamilyMemberId = useUiStore((state) => state.setSelectedFamilyMemberId);

  const isFamilyLoading = familyMembersQuery.isPending && familyMembersQuery.fetchStatus === "fetching";
  const isDocsLoading = documentsQuery.isPending && documentsQuery.fetchStatus === "fetching";

  if ((isFamilyLoading || isDocsLoading) && !familyMembersQuery.data && !documentsQuery.data) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-36" />
          <Skeleton className="h-4 w-48" />
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (familyMembersQuery.isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive">
        Unable to load family overview.
      </div>
    );
  }

  const familyMembers = familyMembersQuery.data?.items ?? [];
  const documents = documentsQuery.data?.items ?? [];

  if (familyMembers.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-lg font-bold tracking-tight text-foreground">
            Family Overview
          </h2>
          <p className="text-xs text-muted-foreground">
            Select a profile to filter your health records and copilot context.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {familyMembers.map((member, idx) => {
          const memberDocs = documents.filter(
            (d) => d.family_member_id === member.id
          );
          const isSelected = selectedFamilyMemberId === member.id;

          const lastDoc = [...memberDocs].sort(
            (a, b) =>
              new Date(b.document_date ?? b.created_at).getTime() -
              new Date(a.document_date ?? a.created_at).getTime()
          )[0];

          const abnormalLabsCount = memberDocs.reduce((acc, doc) => {
            const labs = doc.metadata?.lab_measurements || [];
            const count = labs.filter((lab) => {
              const numVal = typeof lab.value === "number" ? lab.value : parseFloat(String(lab.value));
              const refLow = typeof lab.reference_low === "number" ? lab.reference_low : parseFloat(String(lab.reference_low));
              const refHigh = typeof lab.reference_high === "number" ? lab.reference_high : parseFloat(String(lab.reference_high));
              return (!isNaN(numVal) && !isNaN(refHigh) && numVal > refHigh) || (!isNaN(numVal) && !isNaN(refLow) && numVal < refLow);
            }).length;
            return acc + count;
          }, 0);

          return (
            <motion.div
              key={member.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: idx * 0.04 }}
              onClick={() => setSelectedFamilyMemberId(isSelected ? null : member.id)}
              className={cn(
                "group relative flex cursor-pointer flex-col justify-between overflow-hidden rounded-2xl border p-4 shadow-tinted transition-all hover:scale-[1.01] hover:shadow-md",
                isSelected
                  ? "border-brand-accent bg-accent/40 ring-2 ring-brand-accent/30"
                  : "border-border/70 bg-card hover:border-brand-accent/40"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Avatar className="size-10 rounded-xl ring-2 ring-border/60">
                    <AvatarFallback className="rounded-xl text-xs font-bold bg-muted text-foreground">
                      {getUserInitials(member.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h3 className="font-heading text-sm font-bold tracking-tight text-foreground group-hover:text-primary">
                        {member.name}
                      </h3>
                      {abnormalLabsCount > 0 ? (
                        <span className="flex size-2 rounded-full bg-amber-500 animate-pulse" title={`${abnormalLabsCount} abnormal lab finding(s)`} />
                      ) : null}
                    </div>
                    <span className="inline-block rounded-md bg-muted/60 px-2 py-0.5 text-[0.6875rem] font-medium text-muted-foreground capitalize mt-0.5">
                      {formatRelationship(member.relationship_type)}
                    </span>
                  </div>
                </div>

                <ChevronRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </div>

              <div className="mt-4 pt-3 border-t border-border/40 flex items-center justify-between text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <FileText className="size-3.5" />
                  <span>{memberDocs.length} report{memberDocs.length === 1 ? "" : "s"}</span>
                </div>

                <div>
                  {lastDoc ? (
                    <span>Last: {formatDate(lastDoc.document_date ?? lastDoc.created_at)}</span>
                  ) : (
                    <span>No records</span>
                  )}
                </div>
              </div>

              <div className="mt-2.5">
                {abnormalLabsCount > 0 ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[0.6875rem] font-medium text-amber-700 dark:text-amber-300">
                    <AlertTriangle className="size-3" />
                    {abnormalLabsCount} Abnormal Value{abnormalLabsCount === 1 ? "" : "s"}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[0.6875rem] font-medium text-emerald-700 dark:text-emerald-300">
                    <ShieldCheck className="size-3" />
                    All clear
                  </span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
