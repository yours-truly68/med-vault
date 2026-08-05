"use client";

import { motion } from "framer-motion";
import { FileHeart, Pill, AlertTriangle, Calendar, ShieldCheck } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocuments } from "@/hooks/use-documents";
import { useUiStore } from "@/stores/ui-store";
import { determineLabStatus } from "../chat/lab-values-grid";

export function ClinicalSnapshotCard() {
  const documentsQuery = useDocuments();
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);

  if (documentsQuery.isPending && documentsQuery.fetchStatus === "fetching" && !documentsQuery.data) {
    return <Skeleton className="h-64 w-full rounded-2xl" />;
  }

  if (documentsQuery.isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive">
        Unable to load clinical health snapshot.
      </div>
    );
  }

  const documents = documentsQuery.data?.items ?? [];
  const activeDocs = selectedFamilyMemberId
    ? documents.filter((d) => d.family_member_id === selectedFamilyMemberId)
    : documents;

  const diagnoses = [
    ...new Set(
      activeDocs
        .map((doc) => doc.metadata?.diagnosis)
        .filter((value): value is string => Boolean(value))
    ),
  ].slice(0, 4);

  const medications = activeDocs
    .flatMap((doc) => doc.metadata?.medicines ?? [])
    .map((med) => med.name)
    .filter((name, index, arr) => arr.indexOf(name) === index)
    .slice(0, 6);

  const followUps = activeDocs
    .filter((doc) => doc.metadata?.follow_up)
    .slice(0, 3);

  const abnormalLabs = activeDocs.flatMap((doc) => {
    const labs = doc.metadata?.lab_measurements || [];
    return labs.filter((lab) => {
      const { status } = determineLabStatus(lab);
      return status === "high" || status === "low";
    });
  }).slice(0, 4);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.1 }}
      className="rounded-2xl border border-border/70 bg-card p-5 shadow-tinted space-y-4"
    >
      <div className="flex items-center justify-between border-b border-border/50 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-accent text-primary">
            <FileHeart className="size-4 text-brand-accent" />
          </div>
          <h2 className="font-heading text-base font-bold tracking-tight text-foreground">
            Health Snapshot
          </h2>
        </div>
        <span className="text-[0.6875rem] font-medium text-muted-foreground">
          Extracted Clinical Data
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Active Conditions */}
        <div className="space-y-1.5 rounded-xl border border-border/50 bg-muted/20 p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <FileHeart className="size-3.5 text-primary" />
            <span>Active Conditions & Diagnoses</span>
          </div>
          {diagnoses.length > 0 ? (
            <ul className="space-y-1 pl-1">
              {diagnoses.map((diag, i) => (
                <li key={i} className="text-xs font-semibold text-foreground bg-card px-2 py-1 rounded border border-border/40">
                  • {diag}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">No active diagnoses recorded yet.</p>
          )}
        </div>

        {/* Current Medications */}
        <div className="space-y-1.5 rounded-xl border border-border/50 bg-muted/20 p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <Pill className="size-3.5 text-primary" />
            <span>Current Prescribed Medications</span>
          </div>
          {medications.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {medications.map((med, i) => (
                <span key={i} className="inline-flex items-center gap-1 rounded-md bg-card px-2 py-1 text-xs font-medium text-foreground border border-border/40">
                  <span className="size-1.5 rounded-full bg-brand-accent" />
                  {med}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No active prescriptions found.</p>
          )}
        </div>

        {/* Abnormal Findings */}
        <div className="space-y-1.5 rounded-xl border border-border/50 bg-muted/20 p-3 sm:col-span-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
            <AlertTriangle className="size-3.5 text-amber-500" />
            <span>Abnormal Laboratory Values</span>
          </div>
          {abnormalLabs.length > 0 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {abnormalLabs.map((lab, i) => {
                const { label, badgeClass } = determineLabStatus(lab);
                return (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-card p-2 border border-border/40 text-xs">
                    <div>
                      <span className="font-semibold text-foreground">{lab.test_name}: </span>
                      <span className="font-bold text-foreground">{lab.value} {lab.unit ?? ""}</span>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[0.625rem] font-bold ${badgeClass}`}>
                      {label}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              <ShieldCheck className="size-4" />
              <span>All tested lab measurements are within normal reference ranges.</span>
            </div>
          )}
        </div>

        {/* Follow-up Notes */}
        {followUps.length > 0 ? (
          <div className="space-y-1.5 rounded-xl border border-border/50 bg-muted/20 p-3 sm:col-span-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
              <Calendar className="size-3.5 text-blue-500" />
              <span>Follow-up Recommendations</span>
            </div>
            <ul className="space-y-1">
              {followUps.map((doc) => (
                <li key={doc.id} className="text-xs text-muted-foreground bg-card p-2 rounded border border-border/40 line-clamp-2">
                  {doc.metadata?.follow_up}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
