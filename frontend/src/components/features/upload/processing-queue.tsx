"use client";

import Link from "next/link";
import { CheckCircle2, CircleAlert } from "lucide-react";

import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { DocumentTypeBadge } from "@/components/documents/document-type-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  formatProcessingError,
  formatRelativeTime,
} from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Document, FamilyMember } from "@/types/api";

type ProcessingQueueProps = {
  documents: Document[];
  memberMap: Map<string, FamilyMember>;
  isLoading?: boolean;
};

function isActive(document: Document): boolean {
  return (
    document.status === "pending" ||
    document.status === "processing" ||
    document.status === "failed" ||
    document.status === "rejected"
  );
}

function StatusGlyph({ status }: { status: Document["status"] }) {
  if (status === "completed") {
    return <CheckCircle2 className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden />;
  }
  if (status === "failed") {
    return <CircleAlert className="size-4 text-destructive" aria-hidden />;
  }
  if (status === "rejected") {
    return <CircleAlert className="size-4 text-orange-600 dark:text-orange-400" aria-hidden />;
  }
  return (
    <span
      className="mt-0.5 flex size-4 items-center justify-center"
      aria-hidden
    >
      <span className="status-pulse-dot size-2.5 rounded-full bg-primary" />
    </span>
  );
}

function QueueRow({
  document,
  memberName,
}: {
  document: Document;
  memberName?: string;
}) {
  const busy =
    document.status === "pending" || document.status === "processing";

  return (
    <li>
      <Link
        href={`/documents/${document.id}`}
        className={cn(
          "group block rounded-lg border border-border/70 bg-background/40 px-3 py-3 transition-[background-color,border-color,transform] duration-200",
          "hover:border-border hover:bg-muted/40 active:scale-[0.99]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          document.status === "failed" && "border-destructive/30",
          document.status === "rejected" && "border-orange-500/30",
        )}
      >
        <div className="flex items-start gap-3">
          <div className="mt-0.5 shrink-0">
            <StatusGlyph status={document.status} />
          </div>
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <p
                className="line-clamp-2 min-w-0 flex-1 break-all text-sm font-medium leading-snug"
                title={document.original_filename}
              >
                {document.original_filename}
              </p>
              <DocumentStatusBadge
                status={document.status}
                className="shrink-0"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {document.document_type ? (
                <DocumentTypeBadge type={document.document_type} />
              ) : null}
              {memberName ? (
                <span className="text-xs text-muted-foreground">{memberName}</span>
              ) : null}
              <span className="text-xs text-muted-foreground/80 tabular-nums">
                {formatRelativeTime(document.updated_at || document.created_at)}
              </span>
            </div>

            {busy ? (
              <div className="space-y-1.5">
                <p className="text-xs text-muted-foreground">
                  Extracting text, classifying, and summarizing
                </p>
                <div
                  className="status-shimmer-bar h-1 overflow-hidden rounded-full"
                  aria-hidden
                />
              </div>
            ) : null}

            {document.status === "failed" ? (
              <p className="text-xs leading-relaxed text-destructive/90 text-pretty">
                {formatProcessingError(document.processing_error)}
              </p>
            ) : null}

            {document.status === "rejected" ? (
              <p className="text-xs leading-relaxed text-orange-800 dark:text-orange-200 text-pretty">
                {formatProcessingError(document.processing_error)} Open the
                document and delete it.
              </p>
            ) : null}

            {document.status === "completed" && document.summary?.short_summary ? (
              <p className="line-clamp-2 text-xs leading-relaxed text-muted-foreground text-pretty">
                {document.summary.short_summary}
              </p>
            ) : null}
          </div>
        </div>
      </Link>
    </li>
  );
}

export function ProcessingQueue({
  documents,
  memberMap,
  isLoading,
}: ProcessingQueueProps) {
  const sorted = [...documents].sort(
    (a, b) =>
      new Date(b.updated_at || b.created_at).getTime() -
      new Date(a.updated_at || a.created_at).getTime(),
  );

  const active = sorted.filter(isActive);
  const recentDone = sorted
    .filter((doc) => doc.status === "completed")
    .slice(0, 4);

  const activeCount = active.filter(
    (doc) => doc.status === "pending" || doc.status === "processing",
  ).length;
  const failedCount = active.filter((doc) => doc.status === "failed").length;
  const rejectedCount = active.filter((doc) => doc.status === "rejected").length;

  return (
    <Card className="h-full border-border/70 bg-card/80 shadow-tinted">
      <CardHeader className="space-y-1">
        <CardTitle>Processing status</CardTitle>
        <CardDescription>
          Unfinished uploads stay here beside the form until they finish, fail,
          or get rejected.
        </CardDescription>
        {!isLoading && (activeCount > 0 || failedCount > 0 || rejectedCount > 0) ? (
          <p className="pt-1 text-xs text-muted-foreground tabular-nums">
            {activeCount > 0 ? `${activeCount} in progress` : null}
            {activeCount > 0 && (failedCount > 0 || rejectedCount > 0)
              ? " · "
              : null}
            {failedCount > 0 ? `${failedCount} failed` : null}
            {failedCount > 0 && rejectedCount > 0 ? " · " : null}
            {rejectedCount > 0 ? `${rejectedCount} to delete` : null}
          </p>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-5">
        {isLoading ? (
          <div className="space-y-3" aria-busy="true" aria-label="Loading status">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="h-[4.5rem] animate-pulse rounded-lg bg-muted/60"
              />
            ))}
          </div>
        ) : null}

        {!isLoading && active.length === 0 && recentDone.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/80 bg-muted/15 px-4 py-8 text-center">
            <p className="text-sm font-medium">No uploads in the queue</p>
            <p className="mt-1 text-xs text-muted-foreground text-pretty">
              After you upload, pending and processing files appear here in real
              time.
            </p>
          </div>
        ) : null}

        {!isLoading && active.length > 0 ? (
          <section className="space-y-3" aria-label="Needs attention">
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              In progress
            </h3>
            <ul className="space-y-2.5">
              {active.map((document) => (
                <QueueRow
                  key={document.id}
                  document={document}
                  memberName={memberMap.get(document.family_member_id)?.name}
                />
              ))}
            </ul>
          </section>
        ) : null}

        {!isLoading && recentDone.length > 0 ? (
          <section className="space-y-3" aria-label="Recently processed">
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Recently processed
            </h3>
            <ul className="space-y-2.5">
              {recentDone.map((document) => (
                <QueueRow
                  key={document.id}
                  document={document}
                  memberName={memberMap.get(document.family_member_id)?.name}
                />
              ))}
            </ul>
          </section>
        ) : null}
      </CardContent>
    </Card>
  );
}
