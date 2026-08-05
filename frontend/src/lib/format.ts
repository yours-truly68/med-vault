import type { DocumentStatus, DocumentType, RelationshipType } from "@/types/api";

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  prescription: "Prescription",
  lab_report: "Lab Report",
  hospital_bill: "Hospital Bill",
  pharmacy_bill: "Pharmacy Bill",
  discharge_summary: "Discharge Summary",
  imaging_report: "Imaging Report",
  other: "Other medical",
  unrelated: "Not medical",
};

const DOCUMENT_STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pending",
  uploaded: "Uploaded",
  queued: "Queued",
  processing: "Processing",
  ready: "Ready",
  indexing: "Indexing",
  indexed: "Indexed",
  completed: "Completed",
  failed: "Failed",
  rejected: "Rejected",
};

const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  self: "Self",
  mother: "Mother",
  father: "Father",
  child: "Child",
  spouse: "Spouse",
  other: "Other",
};

export function formatDocumentType(type: DocumentType | null | undefined): string {
  if (!type) return "Unknown";
  return DOCUMENT_TYPE_LABELS[type];
}

export function formatDocumentStatus(status: DocumentStatus): string {
  return DOCUMENT_STATUS_LABELS[status];
}

export function formatRelationship(type: RelationshipType): string {
  return RELATIONSHIP_LABELS[type];
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value.includes("T") ? value : `${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatRelativeTime(value: string): string {
  const date = new Date(value);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;

  return formatDate(value);
}

/** User-facing copy for processing failures; hides raw API payloads. */
export function formatProcessingError(
  error: string | null | undefined,
): string {
  if (!error) return "Processing failed. Open the document to retry.";

  const lower = error.toLowerCase();

  if (
    lower.includes("429") ||
    lower.includes("rate limit") ||
    lower.includes("free tier")
  ) {
    return "AI processing hit a rate limit. Try again in a few minutes.";
  }

  if (
    lower.includes("timeout") ||
    lower.includes("timed out") ||
    lower.includes("etimedout")
  ) {
    return "Processing timed out. Open the document and try again.";
  }

  if (
    lower.includes("api key") ||
    lower.includes("unauthorized") ||
    lower.includes("401") ||
    lower.includes("403")
  ) {
    return "AI service is not configured correctly. Check settings and retry.";
  }

  if (lower.includes("ocr") || lower.includes("extract")) {
    return "We could not read text from this file. Try a clearer scan or PDF.";
  }

  if (
    lower.includes("not look like a medical") ||
    lower.includes("not indexed") ||
    lower.includes("unrelated")
  ) {
    return error.length > 220 ? `${error.slice(0, 217).trimEnd()}...` : error;
  }

  // Strip JSON / HTTP noise for anything else
  if (error.includes("{") || error.includes("API error")) {
    return "Processing failed. Open the document to retry.";
  }

  if (error.length > 120) {
    return `${error.slice(0, 117).trimEnd()}...`;
  }

  return error;
}
