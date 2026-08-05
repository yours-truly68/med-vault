"use client";

import { motion } from "framer-motion";
import { Sparkles, Upload, Clock, Search, FileText, Users, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const ONBOARDING_HIGHLIGHTS = [
  {
    title: "Document Ingestion & OCR",
    desc: "Extracts text & tables from PDFs using PyMuPDF and Tesseract.",
    icon: Upload,
    color: "text-purple-600 bg-purple-500/10",
  },
  {
    title: "Clinical Metadata & Range Tracking",
    desc: "Flags lab results above/below reference ranges automatically.",
    icon: FileText,
    color: "text-amber-600 bg-amber-500/10",
  },
  {
    title: "Chronological Medical Timeline",
    desc: "Organizes visits, lab panels, and procedures into a unified timeline.",
    icon: Clock,
    color: "text-blue-600 bg-blue-500/10",
  },
  {
    title: "Grounded RAG Search",
    desc: "Answers questions with 100% grounded document citations.",
    icon: Search,
    color: "text-emerald-600 bg-emerald-500/10",
  },
] as const;

export function CopilotOnboardingCard({
  onDismiss,
  onSelectPrompt,
}: {
  onDismiss: () => void;
  onSelectPrompt: (prompt: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.25 }}
      className="rounded-2xl border border-border/80 bg-gradient-to-b from-card via-background to-card p-5 shadow-tinted space-y-4"
    >
      <div className="flex items-center gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/30">
          <Sparkles className="size-5 text-brand-accent animate-pulse" />
        </div>
        <div>
          <h3 className="font-heading text-base font-bold tracking-tight text-foreground">
            Welcome to MedVault Copilot!
          </h3>
          <p className="text-xs text-muted-foreground">
            Your universal AI medical assistant available across every page.
          </p>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {ONBOARDING_HIGHLIGHTS.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.title}
              className="flex items-start gap-2.5 rounded-xl border border-border/50 bg-muted/20 p-2.5"
            >
              <div className={`mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-lg ${item.color}`}>
                <Icon className="size-3.5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-foreground">{item.title}</p>
                <p className="text-[0.6875rem] text-muted-foreground leading-tight mt-0.5">
                  {item.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-2 border-t border-border/40 flex items-center justify-between gap-3">
        <Button
          type="button"
          size="sm"
          onClick={() => {
            onDismiss();
            onSelectPrompt("What are my latest blood report results?");
          }}
          className="rounded-xl text-xs gap-1.5 font-medium"
        >
          <span>Ask First Question</span>
          <ArrowRight className="size-3.5" />
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="text-xs text-muted-foreground"
        >
          Dismiss
        </Button>
      </div>
    </motion.div>
  );
}
