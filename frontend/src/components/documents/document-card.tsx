import Link from "next/link";
import { FileText } from "lucide-react";

import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { DocumentTypeBadge } from "@/components/documents/document-type-badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  formatDate,
  formatFileSize,
  formatProcessingError,
  formatRelativeTime,
} from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Document, FamilyMember } from "@/types/api";

type DocumentCardProps = {
  document: Document;
  familyMember?: FamilyMember;
  href?: string;
};

function cardSnippet(document: Document): {
  text: string;
  tone: "default" | "error";
} {
  if (document.status === "failed") {
    return {
      text: formatProcessingError(document.processing_error),
      tone: "error",
    };
  }

  if (document.status === "rejected") {
    return {
      text:
        formatProcessingError(document.processing_error) ||
        "Not a medical record — delete this file.",
      tone: "error",
    };
  }

  if (document.summary?.short_summary) {
    return { text: document.summary.short_summary, tone: "default" };
  }

  if (document.status === "pending" || document.status === "processing") {
    return {
      text: "Extracting text and summary. This usually takes a minute.",
      tone: "default",
    };
  }

  return {
    text: "No summary yet for this document.",
    tone: "default",
  };
}

export function DocumentCard({
  document,
  familyMember,
  href,
}: DocumentCardProps) {
  const snippet = cardSnippet(document);
  const title = document.original_filename;

  const content = (
    <Card
      className={cn(
        "interactive-card flex h-full flex-col border-border/70 bg-card shadow-tinted",
        document.status === "failed" && "border-destructive/25",
        document.status === "rejected" && "border-orange-500/30",
      )}
    >
      <CardHeader className="gap-3 space-y-0">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-accent text-primary ring-1 ring-brand-accent/20">
            <FileText className="size-3.5" aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <CardTitle
                className="line-clamp-2 min-w-0 flex-1 break-all text-[0.9375rem] leading-snug font-semibold tracking-tight"
                title={title}
              >
                {title}
              </CardTitle>
              <DocumentStatusBadge
                status={document.status}
                className="mt-0.5 shrink-0"
              />
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <DocumentTypeBadge type={document.document_type} />
          {familyMember ? (
            <span className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {familyMember.name}
            </span>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="mt-auto flex flex-1 flex-col gap-3 pt-0 text-sm text-muted-foreground">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs tabular-nums">
          <span>
            {formatDate(
              document.document_date ?? document.metadata?.document_date,
            )}
          </span>
          <span className="text-border" aria-hidden>
            |
          </span>
          <span>{formatFileSize(document.file_size_bytes)}</span>
        </div>
        <p
          className={cn(
            "line-clamp-2 min-h-[2.5rem] text-xs leading-relaxed text-pretty",
            snippet.tone === "error"
              ? "text-destructive/90"
              : "text-muted-foreground",
          )}
        >
          {snippet.text}
        </p>
        <p className="mt-auto text-[0.6875rem] text-muted-foreground/80">
          Uploaded {formatRelativeTime(document.created_at)}
        </p>
      </CardContent>
    </Card>
  );

  if (href) {
    return (
      <Link
        href={href}
        className="group block h-full rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        {content}
      </Link>
    );
  }

  return content;
}
