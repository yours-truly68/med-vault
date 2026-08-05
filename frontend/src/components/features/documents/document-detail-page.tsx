"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, CalendarDays, FileText, Trash2, User } from "lucide-react";
import type { ReactNode } from "react";

import { DocumentStatusBadge } from "@/components/documents";
import { DocumentTypeBadge } from "@/components/documents/document-type-badge";
import { ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useDeleteDocument,
  useDocument,
  useReprocessDocument,
} from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import {
  formatDate,
  formatDateTime,
  formatDocumentType,
  formatFileSize,
  formatProcessingError,
} from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Document, DocumentSummary, FamilyMember } from "@/types/api";

type DocumentDetailPageContentProps = {
  documentId: string;
};

function filenameStem(filename: string): string {
  return filename.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").trim();
}

function documentPageTitle(
  document: Document,
  familyMember?: FamilyMember,
): string {
  const typeLabel = formatDocumentType(document.document_type);
  if (document.document_type && document.document_type !== "other") {
    if (familyMember?.name) {
      return `${typeLabel} for ${familyMember.name}`;
    }
    if (document.metadata?.patient_name) {
      return `${typeLabel} for ${document.metadata.patient_name}`;
    }
    return typeLabel;
  }
  return filenameStem(document.original_filename) || document.original_filename;
}

function splitExtractedText(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);
}

function MetaChip({
  icon: Icon,
  children,
}: {
  icon: typeof User;
  children: ReactNode;
}) {
  return (
    <span className="inline-flex max-w-full items-center gap-1.5 text-xs text-muted-foreground">
      <Icon className="size-3.5 shrink-0" aria-hidden />
      <span className="min-w-0 truncate">{children}</span>
    </span>
  );
}

function PanelShell({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "surface-panel flex min-h-0 flex-col overflow-hidden",
        className,
      )}
    >
      <div className="shrink-0 border-b border-border/60 px-4 py-3 sm:px-5">
        <h2 className="font-heading text-base font-semibold tracking-tight text-foreground sm:text-lg">
          {title}
        </h2>
        <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">
          {description}
        </p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5 sm:py-5">
        {children}
      </div>
    </section>
  );
}

function SummarySection({ summary }: { summary: DocumentSummary }) {
  return (
    <PanelShell
      title="Summary"
      description="What this document covers, in plain language"
      className="h-full"
    >
      <div className="space-y-6">
        <p className="text-[0.9375rem] leading-7 text-foreground text-pretty sm:text-base sm:leading-8">
          {summary.short_summary}
        </p>

        {summary.key_findings.length > 0 ? (
          <div>
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Key findings
            </h3>
            <ul className="divide-y divide-border/70 border-y border-border/70">
              {summary.key_findings.map((finding) => (
                <li
                  key={finding}
                  className="py-2.5 text-sm leading-relaxed text-muted-foreground text-pretty"
                >
                  {finding}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {summary.important_dates.length > 0 ? (
          <div>
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Important dates
            </h3>
            <ul className="grid gap-2 sm:grid-cols-2">
              {summary.important_dates.map((item) => (
                <li
                  key={`${item.date}-${item.label}`}
                  className="rounded-md bg-muted/60 px-3 py-2"
                >
                  <p className="text-xs text-muted-foreground">{item.label}</p>
                  <p className="mt-0.5 text-sm font-medium tabular-nums text-foreground">
                    {formatDate(item.date)}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {summary.highlights.length > 0 ? (
          <div>
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Highlights
            </h3>
            <ul className="divide-y divide-border/70 border-y border-border/70">
              {summary.highlights.map((highlight) => (
                <li
                  key={highlight}
                  className="py-2.5 text-sm leading-relaxed text-muted-foreground text-pretty"
                >
                  {highlight}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </PanelShell>
  );
}

function ExtractedTextSection({ text }: { text: string }) {
  const blocks = splitExtractedText(text);

  return (
    <PanelShell
      title="Extracted text"
      description="Full text read from the uploaded file"
      className="h-full"
    >
      {blocks.length > 1 ? (
        <div className="space-y-4">
          {blocks.map((block, index) => (
            <p
              key={`${index}-${block.slice(0, 24)}`}
              className="whitespace-pre-wrap text-sm leading-7 text-foreground/90 text-pretty"
            >
              {block}
            </p>
          ))}
        </div>
      ) : (
        <p className="whitespace-pre-wrap text-sm leading-7 text-foreground/90 text-pretty">
          {text}
        </p>
      )}
    </PanelShell>
  );
}

function RecordDetailsSection({
  document,
  familyMember,
}: {
  document: Document;
  familyMember?: FamilyMember;
}) {
  const metadata = document.metadata;
  const fields = [
    { label: "Patient", value: metadata?.patient_name },
    { label: "Doctor", value: metadata?.doctor_name },
    { label: "Hospital", value: metadata?.hospital_name },
    { label: "Diagnosis", value: metadata?.diagnosis },
    { label: "Specialization", value: metadata?.specialization },
    { label: "Clinical summary", value: metadata?.clinical_summary },
    { label: "Admission", value: formatDate(metadata?.admission_date) },
    { label: "Discharge", value: formatDate(metadata?.discharge_date) },
    { label: "Follow-up", value: metadata?.follow_up },
    {
      label: "Document date",
      value: formatDate(document.document_date ?? metadata?.document_date),
    },
    { label: "Family member", value: familyMember?.name },
    { label: "File size", value: formatFileSize(document.file_size_bytes) },
    { label: "Uploaded", value: formatDateTime(document.created_at) },
    { label: "Original file", value: document.original_filename },
  ].filter((field) => field.value && field.value !== "-");

  return (
    <section className="surface-panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-border/60 px-4 py-3 sm:flex-row sm:items-end sm:justify-between sm:px-5">
        <div>
          <h2 className="font-heading text-base font-semibold tracking-tight text-foreground sm:text-lg">
            Record details
          </h2>
          <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">
            Structured fields pulled from the document
          </p>
        </div>
      </div>

      <div className="px-4 py-4 sm:px-5 sm:py-5">
        {fields.length > 0 ? (
          <dl className="grid gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {fields.map((field) => (
              <div key={field.label} className="min-w-0">
                <dt className="text-xs font-medium text-muted-foreground">
                  {field.label}
                </dt>
                <dd className="mt-1 break-words text-sm font-medium leading-snug text-foreground">
                  {field.value}
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            No structured fields were extracted yet.
          </p>
        )}

        {metadata && metadata.medicines.length > 0 ? (
          <div className="mt-5">
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Medicines
            </h3>
            <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {metadata.medicines.map((medicine) => {
                const detail = [
                  medicine.dosage,
                  medicine.frequency,
                  medicine.duration,
                ]
                  .filter(Boolean)
                  .join(", ");

                return (
                  <li
                    key={`${medicine.name}-${medicine.dosage}`}
                    className="rounded-md bg-muted/50 px-3 py-2"
                  >
                    <p className="text-sm font-medium text-foreground">
                      {medicine.name}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {detail || "No dosage details"}
                    </p>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}

        {metadata && metadata.lab_measurements.length > 0 ? (
          <div className="mt-5">
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Laboratory measurements
            </h3>
            <div className="overflow-x-auto rounded-md border border-border/70">
              <table className="w-full min-w-[28rem] text-left text-sm">
                <thead className="bg-muted/50 text-xs text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Test</th>
                    <th className="px-3 py-2 font-medium">Value</th>
                    <th className="px-3 py-2 font-medium">Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {metadata.lab_measurements.map((lab) => {
                    const reference =
                      lab.reference_low != null && lab.reference_high != null
                        ? `${lab.reference_low}–${lab.reference_high}`
                        : lab.reference_low != null
                          ? `≥ ${lab.reference_low}`
                          : lab.reference_high != null
                            ? `≤ ${lab.reference_high}`
                            : "—";
                    return (
                      <tr
                        key={`${lab.test_name}-${lab.value}`}
                        className="border-t border-border/60"
                      >
                        <td className="px-3 py-2 font-medium">{lab.test_name}</td>
                        <td className="px-3 py-2 tabular-nums">
                          {lab.value}
                          {lab.unit ? ` ${lab.unit}` : ""}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground tabular-nums">
                          {reference}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {metadata && metadata.procedures.length > 0 ? (
          <div className="mt-5">
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Procedures
            </h3>
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {metadata.procedures.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {metadata && metadata.allergies.length > 0 ? (
          <div className="mt-5">
            <h3 className="mb-2 text-sm font-semibold tracking-tight text-foreground">
              Allergies
            </h3>
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {metadata.allergies.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function DocumentDetailPageContent({
  documentId,
}: DocumentDetailPageContentProps) {
  const router = useRouter();
  const documentQuery = useDocument(documentId);
  const familyMembersQuery = useFamilyMembers();
  const deleteMutation = useDeleteDocument();
  const reprocessMutation = useReprocessDocument();

  if (documentQuery.isLoading || familyMembersQuery.isLoading) {
    return <LoadingGrid count={4} />;
  }

  if (documentQuery.isError || !documentQuery.data) {
    return (
      <ErrorState
        message="This document could not be found or you don't have access."
        onRetry={() => void documentQuery.refetch()}
      />
    );
  }

  const document = documentQuery.data;
  const familyMember = familyMembersQuery.data?.items.find(
    (member) => member.id === document.family_member_id,
  );
  const pageTitle = documentPageTitle(document, familyMember);
  const pageDescription = [
    formatDocumentType(document.document_type),
    familyMember?.name,
    formatDate(document.document_date ?? document.metadata?.document_date),
  ]
    .filter(Boolean)
    .join(" · ");

  const hasSummary = Boolean(document.summary);
  const hasExtractedText = Boolean(document.extracted_text?.trim());
  const showEmptyPrimary =
    !hasSummary &&
    !hasExtractedText &&
    document.status !== "failed" &&
    document.status !== "rejected" &&
    (document.status === "pending" || document.status === "processing");
  const showBothPrimary = hasSummary && hasExtractedText;
  const showOnePrimary = (hasSummary || hasExtractedText) && !showBothPrimary;

  const handleDelete = () => {
    if (
      !window.confirm(
        `Delete "${document.original_filename}"? This removes the file, database row, and any embeddings.`,
      )
    ) {
      return;
    }
    deleteMutation.mutate(document.id, {
      onSuccess: () => router.push("/documents"),
    });
  };

  return (
    <div className="flex flex-col gap-4 lg:gap-5">
      <PageHeader
        className="mb-0 border-b-0 pb-0"
        title={pageTitle}
        description={pageDescription || document.original_filename}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" asChild>
              <Link href="/documents">
                <ArrowLeft className="size-4" />
                Back
              </Link>
            </Button>
            {(document.status === "failed" ||
              document.status === "rejected") && (
              <Button
                variant="outline"
                disabled={reprocessMutation.isPending}
                onClick={() => reprocessMutation.mutate(document.id)}
              >
                {reprocessMutation.isPending ? "Reprocessing..." : "Reprocess"}
              </Button>
            )}
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={handleDelete}
            >
              <Trash2 className="size-4" />
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <DocumentStatusBadge status={document.status} />
        <DocumentTypeBadge type={document.document_type} />
        {familyMember ? (
          <MetaChip icon={User}>{familyMember.name}</MetaChip>
        ) : null}
        <MetaChip icon={CalendarDays}>
          {formatDate(
            document.document_date ?? document.metadata?.document_date,
          )}
        </MetaChip>
        <MetaChip icon={FileText}>{document.original_filename}</MetaChip>
      </div>

      {document.status === "rejected" ? (
        <Card className="border-orange-500/35 bg-orange-500/8 shadow-tinted">
          <CardHeader className="gap-3 py-4">
            <CardTitle className="text-base text-orange-900 dark:text-orange-200">
              Not a medical record — delete this file
            </CardTitle>
            <p className="text-sm leading-relaxed text-orange-900/85 dark:text-orange-100/85">
              {formatProcessingError(document.processing_error)}
            </p>
            <div>
              <Button
                variant="destructive"
                size="sm"
                disabled={deleteMutation.isPending}
                onClick={handleDelete}
              >
                <Trash2 className="size-4" />
                {deleteMutation.isPending ? "Deleting..." : "Delete now"}
              </Button>
            </div>
          </CardHeader>
        </Card>
      ) : null}

      {document.processing_error && document.status === "failed" ? (
        <Card className="border-destructive/30 bg-destructive/5 shadow-tinted">
          <CardHeader className="gap-1 py-4">
            <CardTitle className="text-base text-destructive">
              Processing failed
            </CardTitle>
            <p className="text-sm leading-relaxed text-destructive/85">
              {formatProcessingError(document.processing_error)}
            </p>
          </CardHeader>
        </Card>
      ) : null}

      {showEmptyPrimary ? (
        <section className="surface-panel px-5 py-10 text-center">
          <p className="font-heading text-base font-semibold tracking-tight">
            Still processing
          </p>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground text-pretty">
            Summary and extracted text will appear here when OCR and AI
            extraction finish.
          </p>
        </section>
      ) : null}

      {!hasSummary && !hasExtractedText && document.status === "completed" ? (
        <section className="surface-panel px-5 py-8 text-center">
          <p className="text-sm text-muted-foreground">
            No summary or extracted text is available for this document.
          </p>
        </section>
      ) : null}

      {/* Large screens: side-by-side workspace, pane scroll instead of page scroll */}
      {showBothPrimary ? (
        <div className="grid gap-4 lg:h-[min(70dvh,44rem)] lg:grid-cols-2 lg:gap-5">
          <SummarySection summary={document.summary!} />
          <ExtractedTextSection text={document.extracted_text!} />
        </div>
      ) : null}

      {showOnePrimary ? (
        <div className="grid gap-4 lg:h-[min(70dvh,44rem)] lg:grid-cols-1">
          {hasSummary ? <SummarySection summary={document.summary!} /> : null}
          {hasExtractedText ? (
            <ExtractedTextSection text={document.extracted_text!} />
          ) : null}
        </div>
      ) : null}

      <RecordDetailsSection document={document} familyMember={familyMember} />
    </div>
  );
}
