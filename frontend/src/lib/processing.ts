import type {
  Document,
  ProcessingJobStatus,
  ProcessingStage,
} from "@/types/api";

export const PROCESSING_PIPELINE_STEPS: {
  stage: ProcessingStage;
  label: string;
  description: string;
}[] = [
  {
    stage: "uploaded",
    label: "Uploaded",
    description: "File saved and queued for processing",
  },
  {
    stage: "ocr",
    label: "Reading document",
    description: "Extracting text from PDF or image (parallel OCR when needed)",
  },
  {
    stage: "classification",
    label: "Classifying",
    description: "Identifying document type (lab, prescription, etc.)",
  },
  {
    stage: "metadata_summary",
    label: "Extracting details & summary",
    description: "Pulling medicines, labs, diagnoses, and writing a summary in parallel",
  },
  {
    stage: "embeddings",
    label: "Indexing for search",
    description: "Creating embeddings for search and chat",
  },
  {
    stage: "ready",
    label: "Ready",
    description: "Document is searchable and fully processed",
  },
];

const STAGE_ORDER = PROCESSING_PIPELINE_STEPS.map((step) => step.stage);

const LEGACY_STAGE_MAP: Partial<Record<ProcessingStage, ProcessingStage>> = {
  metadata: "metadata_summary",
  summary: "metadata_summary",
};

export function normalizeProcessingStage(stage: ProcessingStage): ProcessingStage {
  return LEGACY_STAGE_MAP[stage] ?? stage;
}

export function getProcessingStageIndex(stage: ProcessingStage): number {
  const normalized = normalizeProcessingStage(stage);
  const index = STAGE_ORDER.indexOf(normalized);
  return index === -1 ? 0 : index;
}

export function formatProcessingStage(stage: ProcessingStage): string {
  const normalized = normalizeProcessingStage(stage);
  return (
    PROCESSING_PIPELINE_STEPS.find((step) => step.stage === normalized)?.label ??
    stage.replace(/_/g, " ")
  );
}

export function getProcessingStageDescription(stage: ProcessingStage): string {
  const normalized = normalizeProcessingStage(stage);
  return (
    PROCESSING_PIPELINE_STEPS.find((step) => step.stage === normalized)?.description ??
    "Processing your document"
  );
}

export function isDocumentProcessing(document: Document): boolean {
  if (document.status === "pending" || document.status === "processing") {
    return true;
  }

  if (document.processing_job?.status === "rate_limited") {
    return true;
  }

  return (
    document.status === "completed" &&
    document.processing_status === "embeddings"
  );
}

export function isRateLimitedJob(document: Document): boolean {
  return document.processing_job?.status === "rate_limited";
}

export function getActiveProcessingStage(document: Document): ProcessingStage {
  const stage = document.processing_job?.stage ?? document.processing_status ?? "uploaded";
  return normalizeProcessingStage(stage);
}

export function getProcessingStatusMessage(document: Document): string {
  if (document.status === "failed") {
    return "Processing failed";
  }
  if (document.processing_job?.status === "paused") {
    return "Processing paused";
  }
  if (document.processing_job?.status === "rate_limited") {
    return "Waiting for AI rate limit — retry scheduled automatically";
  }
  if (document.status === "pending") {
    return "Queued — waiting to start";
  }

  const stage = getActiveProcessingStage(document);
  const label = formatProcessingStage(stage);
  const isLlmStage = [
    "classification",
    "metadata_summary",
    "metadata",
    "summary",
    "embeddings",
  ].includes(stage);

  if (isLlmStage) {
    return `${label} — using AI (this step can take a minute)`;
  }

  return label;
}

export function isRateLimitError(error: string | null | undefined): boolean {
  if (!error) return false;
  const lower = error.toLowerCase();
  return (
    lower.includes("429") ||
    lower.includes("rate limit") ||
    lower.includes("free tier") ||
    lower.includes("quota") ||
    lower.includes("waiting for")
  );
}

export function formatJobStatus(status: ProcessingJobStatus): string {
  switch (status) {
    case "pending":
      return "Queued";
    case "running":
      return "In progress";
    case "paused":
      return "Paused";
    case "rate_limited":
      return "Waiting for rate limit";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

export function getRetryCountdownSeconds(
  nextRetryAt: string | null | undefined,
): number | null {
  if (!nextRetryAt) return null;
  const target = new Date(nextRetryAt).getTime();
  if (Number.isNaN(target)) return null;
  const seconds = Math.max(0, Math.ceil((target - Date.now()) / 1000));
  return seconds;
}
