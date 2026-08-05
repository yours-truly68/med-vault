"use client";

import { Clock3 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useUiStore } from "@/stores/ui-store";

export function LlmBusyBanner() {
  const visible = useUiStore((state) => state.llmBusyBannerVisible);
  const detail = useUiStore((state) => state.llmBusyDetail);
  const source = useUiStore((state) => state.llmBusySource);
  const acknowledge = useUiStore((state) => state.acknowledgeLlmBusy);

  if (!visible) return null;

  const contextLabel =
    source === "chat"
      ? "Chat answers are paused for now."
      : source === "processing"
        ? "Document processing is waiting on the AI provider."
        : "Some AI features are temporarily delayed.";

  return (
    <div
      role="status"
      aria-live="polite"
      className="mb-4 flex flex-col gap-3 rounded-lg border border-amber-500/35 bg-amber-500/10 px-4 py-3 text-amber-950 sm:flex-row sm:items-center sm:justify-between dark:text-amber-50"
    >
      <div className="flex min-w-0 items-start gap-3">
        <Clock3
          className="mt-0.5 size-4 shrink-0 text-amber-700 dark:text-amber-300"
          aria-hidden
        />
        <div className="min-w-0 space-y-1">
          <p className="text-sm font-semibold tracking-tight">
            The AI is busy right now
          </p>
          <p className="text-xs leading-relaxed text-amber-900/80 dark:text-amber-100/80">
            {contextLabel} Please try again in a little while
            {detail ? ` — ${detail}` : "."}
          </p>
        </div>
      </div>
      <Button
        type="button"
        size="sm"
        variant="outline"
        className="shrink-0 border-amber-600/40 bg-background/60 text-amber-950 hover:bg-amber-500/15 dark:text-amber-50"
        onClick={acknowledge}
      >
        Acknowledged
      </Button>
    </div>
  );
}
