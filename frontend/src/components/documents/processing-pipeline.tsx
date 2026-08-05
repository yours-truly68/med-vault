"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Circle, Clock3, Loader2, PauseCircle, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  formatJobStatus,
  getActiveProcessingStage,
  getProcessingStageDescription,
  getProcessingStageIndex,
  getRetryCountdownSeconds,
  isDocumentProcessing,
  isRateLimitedJob,
  isRateLimitError,
  PROCESSING_PIPELINE_STEPS,
} from "@/lib/processing";
import { formatProcessingError } from "@/lib/format";
import type { Document } from "@/types/api";

type ProcessingPipelineProps = {
  document: Document;
  className?: string;
  compact?: boolean;
};

export function ProcessingPipeline({
  document,
  className,
  compact = false,
}: ProcessingPipelineProps) {
  const activeStage = getActiveProcessingStage(document);
  const activeIndex = getProcessingStageIndex(activeStage);
  const isFailed = document.status === "failed";
  const isPaused = document.processing_job?.status === "paused";
  const isRateLimited = isRateLimitedJob(document);
  const isActive = isDocumentProcessing(document);
  const errorMessage =
    document.processing_error ?? document.processing_job?.error_message;
  const rateLimited = isRateLimited || isRateLimitError(errorMessage);
  const [retryInSeconds, setRetryInSeconds] = useState<number | null>(
    getRetryCountdownSeconds(document.processing_job?.next_retry_at),
  );

  useEffect(() => {
    if (!isRateLimited) {
      setRetryInSeconds(null);
      return;
    }

    const update = () => {
      setRetryInSeconds(
        getRetryCountdownSeconds(document.processing_job?.next_retry_at),
      );
    };

    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [document.processing_job?.next_retry_at, isRateLimited]);

  if (!isActive && !isFailed && document.status !== "rejected") {
    if (document.status !== "completed") return null;
  }

  const visibleSteps = PROCESSING_PIPELINE_STEPS.filter(
    (step) => step.stage !== "ready" || document.status === "completed",
  );

  return (
    <section
      className={cn(
        "surface-panel overflow-hidden",
        isFailed && "border-destructive/30",
        rateLimited && "border-amber-500/30",
        className,
      )}
      aria-live="polite"
      aria-label="Document processing progress"
    >
      <div className="border-b border-border/60 px-4 py-3 sm:px-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-heading text-base font-semibold tracking-tight">
              {isFailed
                ? "Processing failed"
                : isPaused
                  ? "Processing paused"
                  : rateLimited
                    ? "Waiting for rate limit"
                    : "Processing progress"}
            </h2>
            <p className="mt-0.5 text-sm text-muted-foreground">
              {isFailed
                ? `Failed during ${getProcessingStageDescription(activeStage).toLowerCase()}`
                : rateLimited
                  ? "The AI provider is throttling requests. We will retry automatically."
                  : getProcessingStageDescription(activeStage)}
            </p>
          </div>
          {isActive && !isPaused && !rateLimited ? (
            <Loader2
              className="size-5 shrink-0 animate-spin text-primary"
              aria-hidden
            />
          ) : null}
          {isPaused ? (
            <PauseCircle className="size-5 shrink-0 text-amber-600" aria-hidden />
          ) : null}
          {rateLimited ? (
            <Clock3 className="size-5 shrink-0 text-amber-600" aria-hidden />
          ) : null}
        </div>

        {document.processing_job ? (
          <p className="mt-2 text-xs text-muted-foreground">
            Job status: {formatJobStatus(document.processing_job.status)}
            {document.processing_job.retry_count > 0
              ? ` · Retry ${document.processing_job.retry_count}`
              : ""}
            {rateLimited && retryInSeconds !== null
              ? ` · Retrying in ${retryInSeconds}s`
              : ""}
          </p>
        ) : null}
      </div>

      {!compact ? (
        <ol className="space-y-0 px-4 py-3 sm:px-5">
          {visibleSteps.map((step, index) => {
            const stepIndex = getProcessingStageIndex(step.stage);
            const isComplete =
              (document.status === "completed" &&
                document.processing_status === "ready") ||
              (isActive && stepIndex < activeIndex) ||
              (isFailed && stepIndex < activeIndex);
            const isCurrent =
              !isFailed &&
              isActive &&
              step.stage === activeStage &&
              step.stage !== "ready";
            const isFailedStep = isFailed && step.stage === activeStage;

            return (
              <li
                key={step.stage}
                className={cn(
                  "flex gap-3 border-l-2 py-2.5 pl-4",
                  index === visibleSteps.length - 1 ? "border-transparent" : "",
                  isComplete
                    ? "border-primary/50"
                    : isCurrent
                      ? rateLimited
                        ? "border-amber-500"
                        : "border-primary"
                      : isFailedStep
                        ? "border-destructive"
                        : "border-border/50",
                )}
              >
                <div className="mt-0.5 shrink-0">
                  {isFailedStep ? (
                    <XCircle className="size-4 text-destructive" aria-hidden />
                  ) : isComplete ? (
                    <CheckCircle2 className="size-4 text-primary" aria-hidden />
                  ) : isCurrent ? (
                    rateLimited ? (
                      <Clock3 className="size-4 text-amber-600" aria-hidden />
                    ) : (
                      <Loader2
                        className="size-4 animate-spin text-primary"
                        aria-hidden
                      />
                    )
                  ) : (
                    <Circle className="size-4 text-muted-foreground/50" aria-hidden />
                  )}
                </div>
                <div className="min-w-0">
                  <p
                    className={cn(
                      "text-sm font-medium",
                      isCurrent && "text-foreground",
                      isComplete && "text-foreground/80",
                      !isCurrent && !isComplete && "text-muted-foreground",
                      isFailedStep && "text-destructive",
                      isCurrent && rateLimited && "text-amber-900 dark:text-amber-100",
                    )}
                  >
                    {step.label}
                    {isCurrent && !rateLimited ? " — in progress" : null}
                    {isCurrent && rateLimited ? " — waiting for rate limit" : null}
                  </p>
                  {!compact ? (
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {step.description}
                    </p>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {errorMessage && (isFailed || rateLimited) ? (
        <div
          className={cn(
            "border-t border-border/60 px-4 py-3 text-sm sm:px-5",
            rateLimited
              ? "bg-amber-500/8 text-amber-900 dark:text-amber-100"
              : "bg-destructive/5 text-destructive",
          )}
        >
          {formatProcessingError(errorMessage)}
          {rateLimited ? (
            <p className="mt-1 text-xs opacity-90">
              Your document details are saved. Search indexing will resume automatically
              when the provider allows more requests
              {retryInSeconds !== null ? ` (about ${retryInSeconds}s)` : ""}.
            </p>
          ) : null}
        </div>
      ) : isActive && !isPaused && !rateLimited ? (
        <div className="border-t border-border/60 px-4 py-3 text-xs text-muted-foreground sm:px-5">
          {["classification", "metadata_summary", "metadata", "summary", "embeddings"].includes(
            activeStage,
          )
            ? "AI steps can take 30–90 seconds each. Metadata and summary now run in parallel."
            : "This page refreshes every few seconds while processing."}
        </div>
      ) : null}
    </section>
  );
}
