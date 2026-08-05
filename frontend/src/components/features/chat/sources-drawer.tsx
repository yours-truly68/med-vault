"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, FileText, ExternalLink, Layers, Building2, Stethoscope, User, AlertTriangle } from "lucide-react";
import type { ChatCitation } from "@/types/api";
import { formatDocumentType, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

export function SourcesDrawer({ citations }: { citations: ChatCitation[] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="rounded-xl border border-border/60 bg-muted/20 overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-3.5 py-2.5 text-xs font-medium text-muted-foreground hover:bg-muted/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="flex size-5 items-center justify-center rounded-md bg-accent text-primary">
            <Layers className="size-3" />
          </div>
          <span className="font-semibold text-foreground">
            Supporting Medical Documents ({citations.length})
          </span>
          <span className="hidden text-muted-foreground sm:inline">
            · {citations.map((c) => c.original_filename).slice(0, 2).join(", ")}
            {citations.length > 2 ? ` +${citations.length - 2} more` : ""}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-primary font-medium">
          <span>{isOpen ? "Hide Evidence" : "View Evidence"}</span>
          <ChevronDown
            className={cn("size-4 transition-transform duration-200", isOpen && "rotate-180")}
          />
        </div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
          >
            <div className="border-t border-border/40 p-3 grid gap-2.5 sm:grid-cols-2">
              {citations.map((citation, index) => {
                const matchScore = citation.score ? Math.round(citation.score * 100) : null;
                return (
                  <motion.div
                    key={`${citation.document_id}-${index}`}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15, delay: index * 0.04 }}
                    className="flex flex-col justify-between rounded-xl border border-border/60 bg-card p-3 shadow-sm hover:border-brand-accent/40 transition-all space-y-2"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <FileText className="size-4 shrink-0 text-brand-accent" />
                          <p className="truncate text-xs font-bold text-foreground">
                            {citation.original_filename}
                          </p>
                        </div>
                        {matchScore !== null ? (
                          <span className="shrink-0 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[0.625rem] font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            {matchScore}% confidence
                          </span>
                        ) : null}
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-[0.6875rem] text-muted-foreground">
                        <span className="font-medium text-foreground">{formatDocumentType(citation.document_type)}</span>
                        {citation.document_date ? (
                          <span>· {formatDate(citation.document_date)}</span>
                        ) : null}
                        {citation.page ? <span>· Page {citation.page}</span> : null}
                      </div>

                      {citation.excerpt ? (
                        <p className="line-clamp-3 text-[0.75rem] leading-relaxed text-muted-foreground bg-muted/40 p-2 rounded-lg border border-border/30">
                          &ldquo;{citation.excerpt}&rdquo;
                        </p>
                      ) : null}
                    </div>

                    <div className="pt-2 border-t border-border/30 flex items-center justify-between">
                      <span className="text-[0.625rem] text-muted-foreground">Grounded Citation #{index + 1}</span>
                      <Link
                        href={`/documents/${citation.document_id}`}
                        className="inline-flex items-center gap-1 text-[0.6875rem] font-bold text-primary hover:underline"
                      >
                        <span>Jump to Report</span>
                        <ExternalLink className="size-3" />
                      </Link>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
