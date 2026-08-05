"use client";

import { useState, type MouseEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ArrowRight,
  FileText,
  Building2,
  Stethoscope,
  Activity,
  Pill,
  Calendar,
  User,
  ShieldAlert,
  Microscope,
  ClipboardList,
  Receipt,
  Scan,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

import { DocumentTypeBadge } from "@/components/documents/document-type-badge";
import { formatDate, formatDocumentType } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Document, FamilyMember } from "@/types/api";
import { determineLabStatus } from "../chat/lab-values-grid";
import { useCopilotStore } from "@/stores/copilot-store";

type TimelineRowProps = {
  document: Document;
  familyMember?: FamilyMember;
  index: number;
};

function getClinicalDocumentTitle(document: Document): string {
  if (document.metadata?.diagnosis) {
    return document.metadata.diagnosis;
  }

  if (document.document_type) {
    switch (document.document_type) {
      case "lab_report":
        return "Complete Blood Count & Lab Panel";
      case "prescription":
        return "Clinical Prescription";
      case "discharge_summary":
        return "Hospital Discharge Summary";
      case "hospital_bill":
        return "Hospital Services Bill";
      case "pharmacy_bill":
        return "Pharmacy Invoice";
      case "imaging_report":
        return "Radiology & Imaging Scan";
      default:
        return formatDocumentType(document.document_type);
    }
  }

  return document.original_filename
    .replace(/[-_]/g, " ")
    .replace(/\.[^/.]+$/, "");
}

function getDocumentIcon(docType: Document["document_type"]) {
  switch (docType) {
    case "lab_report":
      return <Microscope className="size-4 text-emerald-600 dark:text-emerald-400" />;
    case "prescription":
      return <Pill className="size-4 text-purple-600 dark:text-purple-400" />;
    case "discharge_summary":
      return <ClipboardList className="size-4 text-blue-600 dark:text-blue-400" />;
    case "hospital_bill":
    case "pharmacy_bill":
      return <Receipt className="size-4 text-amber-600 dark:text-amber-400" />;
    case "imaging_report":
      return <Scan className="size-4 text-cyan-600 dark:text-cyan-400" />;
    default:
      return <FileText className="size-4 text-muted-foreground" />;
  }
}

export function TimelineRow({ document, familyMember, index }: TimelineRowProps) {
  const router = useRouter();
  const [isExpanded, setIsExpanded] = useState(false);
  const toggleCopilot = useCopilotStore((state) => state.toggleCopilot);

  const docDate =
    document.document_date ??
    document.metadata?.document_date ??
    document.created_at.slice(0, 10);

  const meta = document.metadata;
  const summary = document.summary;
  const labs = meta?.lab_measurements || [];

  // Extract abnormal lab values with direction indicators
  const abnormalLabs = labs
    .map((lab) => {
      const { status } = determineLabStatus(lab);
      return { lab, status };
    })
    .filter(({ status }) => status === "high" || status === "low");

  const clinicalTitle = getClinicalDocumentTitle(document);

  const handleRowClick = () => {
    router.push(`/documents/${document.id}`);
  };

  const handleExpandToggle = (e: MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const handleAskCopilot = (e: MouseEvent) => {
    e.stopPropagation();
    toggleCopilot();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, delay: Math.min(index * 0.02, 0.3) }}
      onClick={handleRowClick}
      tabIndex={0}
      role="button"
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleRowClick();
        }
      }}
      className="group relative border-b border-border/50 bg-card/60 px-4 py-3.5 transition-all duration-180 hover:bg-accent/40 hover:border-brand-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        {/* Main Clinical Info */}
        <div className="flex items-start gap-3.5 min-w-0 flex-1">
          {/* Document Type Icon Node */}
          <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-xl bg-accent/80 ring-1 ring-border/60 transition-transform duration-180 group-hover:scale-105 shadow-xs">
            {getDocumentIcon(document.document_type)}
          </div>

          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-heading text-sm font-bold tracking-tight text-foreground group-hover:text-primary transition-colors duration-180">
                {clinicalTitle}
              </span>

              <DocumentTypeBadge type={document.document_type} />

              {/* Meaningful Specific Abnormal Badges */}
              {abnormalLabs.length > 0 ? (
                <div className="flex flex-wrap items-center gap-1">
                  {abnormalLabs.slice(0, 3).map(({ lab, status }) => (
                    <span
                      key={lab.test_name}
                      className={cn(
                        "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[0.6875rem] font-bold border",
                        status === "high"
                          ? "bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/20"
                          : "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20"
                      )}
                    >
                      {status === "high" ? (
                        <ArrowUpRight className="size-3" />
                      ) : (
                        <ArrowDownRight className="size-3" />
                      )}
                      {lab.test_name}
                    </span>
                  ))}

                  {abnormalLabs.length > 3 ? (
                    <span className="rounded-full bg-muted px-1.5 py-0.5 text-[0.625rem] font-semibold text-muted-foreground">
                      +{abnormalLabs.length - 3} more
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>

            {/* Concise Clinical Summary Line */}
            {summary?.short_summary ? (
              <p className="line-clamp-1 text-xs text-muted-foreground leading-relaxed">
                {summary.short_summary}
              </p>
            ) : meta?.diagnosis ? (
              <p className="line-clamp-1 text-xs text-muted-foreground">
                Diagnosis: <span className="font-medium text-foreground">{meta.diagnosis}</span>
              </p>
            ) : null}

            {/* Metadata Pills: Hospital, Doctor, Patient */}
            <div className="flex flex-wrap items-center gap-3 text-[0.6875rem] text-muted-foreground pt-0.5">
              {meta?.hospital_name ? (
                <span className="inline-flex items-center gap-1 font-medium">
                  <Building2 className="size-3 text-brand-accent" />
                  {meta.hospital_name}
                </span>
              ) : null}

              {meta?.doctor_name ? (
                <span className="inline-flex items-center gap-1 font-medium">
                  <Stethoscope className="size-3 text-primary" />
                  {meta.doctor_name}
                </span>
              ) : null}

              {familyMember ? (
                <span className="inline-flex items-center gap-1 font-medium">
                  <User className="size-3 text-muted-foreground" />
                  {familyMember.name}
                </span>
              ) : null}
            </div>
          </div>
        </div>

        {/* Right Action & Date */}
        <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
          <div className="text-left sm:text-right">
            <span className="inline-flex items-center gap-1.5 text-xs font-bold text-foreground">
              <Calendar className="size-3.5 text-muted-foreground sm:hidden" />
              {formatDate(docDate)}
            </span>
          </div>

          <div className="flex items-center gap-1">
            {/* Expand / Collapse Progressive Disclosure Toggle */}
            <button
              type="button"
              onClick={handleExpandToggle}
              className="flex size-7 items-center justify-center rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title={isExpanded ? "Collapse details" : "Expand details"}
            >
              <ChevronDown
                className={cn("size-4 transition-transform duration-200", isExpanded && "rotate-180")}
              />
            </button>

            {/* Primary View Report Link with Animated Arrow */}
            <Link
              href={`/documents/${document.id}`}
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:underline px-2.5 py-1 rounded-lg hover:bg-accent/60 transition-colors"
            >
              <span className="hidden sm:inline">View Report</span>
              <ArrowRight className="size-3.5 transition-transform duration-180 group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* Progressive Disclosure Panel */}
      <AnimatePresence initial={false}>
        {isExpanded ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="mt-3.5 border-t border-border/40 pt-3.5 text-xs space-y-3"
          >
            {/* AI Clinical Summary & Findings */}
            {summary?.short_summary ? (
              <div className="rounded-xl border border-border/40 bg-muted/20 p-3">
                <p className="font-semibold text-foreground mb-1">AI Clinical Summary:</p>
                <p className="text-muted-foreground leading-relaxed">{summary.short_summary}</p>
              </div>
            ) : null}

            {summary?.key_findings?.length ? (
              <div>
                <p className="font-semibold text-muted-foreground mb-1">Key Clinical Findings:</p>
                <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                  {summary.key_findings.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* Abnormal Lab Measurement Detail Grid */}
            {abnormalLabs.length > 0 ? (
              <div>
                <p className="font-semibold text-amber-600 dark:text-amber-400 mb-1.5 flex items-center gap-1">
                  <ShieldAlert className="size-3.5" />
                  Out-of-Range Lab Values ({abnormalLabs.length}):
                </p>
                <div className="grid gap-2 sm:grid-cols-3">
                  {abnormalLabs.map(({ lab, status }, i) => (
                    <div key={i} className="rounded-lg bg-card p-2.5 border border-amber-500/20 shadow-xs">
                      <p className="font-semibold text-foreground truncate">{lab.test_name}</p>
                      <p className="text-xs font-bold text-foreground mt-0.5">
                        {lab.value} {lab.unit ?? ""}
                      </p>
                      <p className="text-[0.6875rem] text-muted-foreground mt-0.5">
                        Ref: {lab.reference_low ?? "?"} - {lab.reference_high ?? "?"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Source File & Action Buttons */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/30 text-[0.6875rem] text-muted-foreground">
              <span>Original File: <code className="font-mono text-foreground">{document.original_filename}</code></span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleAskCopilot}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-brand-accent/30 bg-accent px-2.5 py-1 font-bold text-primary hover:bg-accent/80 transition-colors"
                >
                  <Sparkles className="size-3 text-brand-accent" />
                  <span>Ask Copilot about this report</span>
                </button>

                <Link
                  href={`/documents/${document.id}`}
                  className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1 font-bold text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <span>Open Report</span>
                  <ArrowRight className="size-3" />
                </Link>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
}
