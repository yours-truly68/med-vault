"use client";

import { useEffect, useRef } from "react";

import { useDocuments } from "@/hooks/use-documents";
import {
  isRateLimitedJob,
  isRateLimitError,
} from "@/lib/processing";
import { useUiStore } from "@/stores/ui-store";

/**
 * Watches the document list for rate-limited jobs and surfaces toast + banner.
 * Lives in the dashboard shell so users see it on any page.
 */
export function LlmRateLimitWatcher() {
  const notify = useUiStore((state) => state.notifyLlmRateLimited);
  const { data } = useDocuments({ pollWhileProcessing: true });
  const seenKeysRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const items = data?.items ?? [];
    for (const document of items) {
      const rateLimited =
        isRateLimitedJob(document) ||
        isRateLimitError(
          document.processing_error ?? document.processing_job?.error_message,
        );

      if (!rateLimited) continue;

      const key = [
        document.id,
        document.processing_job?.status ?? document.status,
        document.processing_job?.updated_at ?? document.updated_at,
      ].join(":");

      if (seenKeysRef.current.has(key)) continue;
      seenKeysRef.current.add(key);

      notify({
        key,
        source: "processing",
        detail:
          document.processing_job?.error_message ??
          document.processing_error ??
          undefined,
      });
    }
  }, [data?.items, notify]);

  return null;
}
