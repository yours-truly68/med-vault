"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, Activity, Pill, Clock, Upload, ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

const PROMPT_STARTERS = [
  {
    category: "Lab Results",
    prompt: "What were my latest blood report results?",
    icon: Activity,
    color: "text-amber-600 dark:text-amber-400 bg-amber-500/10",
  },
  {
    category: "Abnormal Values",
    prompt: "Were any lab values outside the reference range?",
    icon: Activity,
    color: "text-red-600 dark:text-red-400 bg-red-500/10",
  },
  {
    category: "Medications",
    prompt: "List all medications and dosages from recent prescriptions.",
    icon: Pill,
    color: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10",
  },
  {
    category: "History & Timeline",
    prompt: "Summarize my health timeline and hospital visits.",
    icon: Clock,
    color: "text-blue-600 dark:text-blue-400 bg-blue-500/10",
  },
] as const;

export function ChatEmptyStateHero({
  onSelectPrompt,
}: {
  onSelectPrompt: (prompt: string) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mx-auto flex h-full max-w-3xl flex-col justify-center px-4 py-8"
    >
      {/* Hero Assistant Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-border/70 bg-gradient-to-b from-accent/50 via-background to-card p-6 shadow-tinted text-center">
        <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-2xl bg-accent text-primary ring-1 ring-brand-accent/30 shadow-md">
          <Sparkles className="size-7 text-brand-accent animate-pulse" />
        </div>

        <h2 className="font-heading text-xl font-bold tracking-tight text-foreground sm:text-2xl">
          MedVault AI Copilot
        </h2>

        <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-muted-foreground sm:text-sm text-pretty">
          Your personal medical document assistant. Answers are strictly grounded in your uploaded records with source citations.
        </p>

        {/* Capabilities Pills */}
        <div className="mt-4 flex flex-wrap justify-center gap-2 text-[0.6875rem] font-medium">
          <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/40 px-2.5 py-1 text-foreground/80">
            <ShieldCheck className="size-3 text-emerald-500" />
            100% Grounded RAG
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/40 px-2.5 py-1 text-foreground/80">
            <Activity className="size-3 text-brand-accent" />
            Lab Panel Range Tracking
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-muted/40 px-2.5 py-1 text-foreground/80">
            <Clock className="size-3 text-blue-500" />
            Timeline Matching
          </span>
        </div>
      </div>

      {/* Categorized Prompt Starters Grid */}
      <div className="mt-6 space-y-2">
        <p className="text-xs font-semibold text-muted-foreground px-1">
          Try asking one of these questions:
        </p>

        <div className="grid gap-2.5 sm:grid-cols-2">
          {PROMPT_STARTERS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.button
                key={item.prompt}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: idx * 0.05 }}
                type="button"
                onClick={() => onSelectPrompt(item.prompt)}
                className="group flex flex-col justify-between rounded-xl border border-border/70 bg-card p-3.5 text-left transition-all hover:border-brand-accent/40 hover:bg-accent/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[0.6875rem] font-semibold ${item.color}`}>
                    <Icon className="size-3" />
                    {item.category}
                  </span>
                  <ArrowRight className="size-3.5 text-muted-foreground opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-0.5" />
                </div>
                <p className="mt-2 text-xs font-medium leading-relaxed text-foreground group-hover:text-primary">
                  &ldquo;{item.prompt}&rdquo;
                </p>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Upload Reminder Banner */}
      <div className="mt-6 flex items-center justify-between rounded-xl border border-border/60 bg-muted/30 p-3.5">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-accent text-primary">
            <Upload className="size-4" />
          </div>
          <div>
            <p className="text-xs font-semibold text-foreground">Need to add new records?</p>
            <p className="text-[0.6875rem] text-muted-foreground">Upload blood reports, prescriptions, or bills.</p>
          </div>
        </div>
        <Button asChild size="sm" variant="outline" className="rounded-xl text-xs gap-1.5">
          <Link href="/upload">
            <span>Upload</span>
            <ArrowRight className="size-3" />
          </Link>
        </Button>
      </div>
    </motion.div>
  );
}
