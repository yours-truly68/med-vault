"use client";

import { useState, useEffect } from "react";
import { Eye, ExternalLink, Download, FileText, Maximize2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

type DocumentPreviewPanelProps = {
  documentId: string;
  originalFilename: string;
  mimeType?: string;
  className?: string;
};

export function DocumentPreviewPanel({
  documentId,
  originalFilename,
  mimeType,
  className,
}: DocumentPreviewPanelProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const accessToken = useAuthStore((state) => state.accessToken);

  useEffect(() => {
    let cancelled = false;

    async function fetchPreviewUrl() {
      setLoading(true);
      setError(null);
      try {
        const token = accessToken || useAuthStore.getState().accessToken;
        const data = await apiClient<{ url: string }>(
          `/documents/${documentId}/presigned-url`,
          { token },
        );
        if (!cancelled) {
          setPreviewUrl(data.url);
        }
      } catch (err) {
        if (!cancelled) {
          setError("Failed to load document preview");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchPreviewUrl();
    return () => {
      cancelled = true;
    };
  }, [documentId, accessToken]);

  const isPdf =
    mimeType === "application/pdf" ||
    originalFilename.toLowerCase().endsWith(".pdf");

  const isImage =
    mimeType?.startsWith("image/") ||
    /\.(jpg|jpeg|png|webp)$/i.test(originalFilename);

  return (
    <section
      className={cn(
        "surface-panel flex flex-col overflow-hidden rounded-2xl border border-border/70 bg-card shadow-tinted",
        isFullscreen ? "fixed inset-4 z-50 shadow-2xl" : "h-[min(680px,65dvh)]",
        className
      )}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-border/60 bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="size-4 text-brand-accent shrink-0" />
          <h3 className="font-heading text-sm font-semibold tracking-tight text-foreground truncate">
            Document Preview — {originalFilename}
          </h3>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Preview"}
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="rounded-lg text-muted-foreground hover:text-foreground"
          >
            <Maximize2 className="size-4" />
          </Button>

          {previewUrl ? (
            <Button variant="outline" size="sm" asChild className="h-7 text-xs gap-1">
              <a href={previewUrl} target="_blank" rel="noopener noreferrer">
                <span>Open File</span>
                <ExternalLink className="size-3" />
              </a>
            </Button>
          ) : null}
        </div>
      </div>

      {/* Preview Canvas */}
      <div className="flex-1 bg-muted/20 overflow-hidden relative flex items-center justify-center p-2">
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
            <Loader2 className="size-6 animate-spin" />
            <p className="text-xs">Loading preview…</p>
          </div>
        ) : error || !previewUrl ? (
          <div className="flex flex-col items-center justify-center text-center p-6 space-y-3">
            <FileText className="size-10 text-muted-foreground" />
            <div>
              <p className="text-sm font-semibold text-foreground">
                {error || "Preview Unavailable"}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Unable to load document preview.
              </p>
            </div>
          </div>
        ) : isPdf ? (
          <iframe
            src={`${previewUrl}#toolbar=1`}
            title={originalFilename}
            className="w-full h-full rounded-xl border border-border/40 shadow-xs"
          />
        ) : isImage ? (
          <div className="w-full h-full flex items-center justify-center overflow-auto p-4">
            <img
              src={previewUrl}
              alt={originalFilename}
              className="max-w-full max-h-full object-contain rounded-xl shadow-md"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-center p-6 space-y-3">
            <FileText className="size-10 text-muted-foreground animate-pulse" />
            <div>
              <p className="text-sm font-semibold text-foreground">
                Document Preview Available
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Click below to download or view the original file.
              </p>
            </div>
            <Button variant="outline" size="sm" asChild className="gap-1.5">
              <a href={previewUrl} download={originalFilename}>
                <Download className="size-3.5" />
                <span>Download {originalFilename}</span>
              </a>
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}

