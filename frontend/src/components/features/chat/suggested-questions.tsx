"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight } from "lucide-react";
import type { ChatAskResponse } from "@/types/api";

export function generateSuggestedQuestions(
  response?: ChatAskResponse
): string[] {
  if (!response) return [];

  const suggestions: string[] = [];
  const details = response.supporting_details;

  if (details?.lab_values && details.lab_values.length > 0) {
    suggestions.push("Compare with previous blood report");
    suggestions.push("Show lab value trend over time");
  }

  if (details?.diagnosis) {
    suggestions.push("Explain diagnosis in plain language");
  }

  if (details?.medicines && details.medicines.length > 0) {
    suggestions.push("List all prescribed medications & dosages");
  }

  if (response.citations && response.citations.length > 0) {
    suggestions.push("What is the report date of this source?");
  }

  // Fallbacks if fewer than 3
  if (suggestions.length < 3) {
    suggestions.push("Were any values outside reference range?");
    suggestions.push("Summarize my recent hospital visit");
  }

  // Deduplicate and slice top 4
  return Array.from(new Set(suggestions)).slice(0, 4);
}

export function SuggestedQuestionsChips({
  response,
  onSelect,
}: {
  response?: ChatAskResponse;
  onSelect: (question: string) => void;
}) {
  const questions = generateSuggestedQuestions(response);

  if (questions.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.15 }}
      className="space-y-2 border-t border-border/50 pt-3"
    >
      <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
        <Sparkles className="size-3.5 text-brand-accent" />
        <span>Suggested Follow-ups</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, idx) => (
          <motion.button
            key={q}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.15, delay: 0.15 + idx * 0.04 }}
            type="button"
            onClick={() => onSelect(q)}
            className="group flex items-center gap-1.5 rounded-full border border-border/70 bg-muted/40 px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-brand-accent/40 hover:bg-accent/60 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <span>{q}</span>
            <ArrowRight className="size-3 transition-transform group-hover:translate-x-0.5" />
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
