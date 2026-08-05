"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Search, FileText, Scale, Sparkles, Loader2 } from "lucide-react";

const THINKING_STEPS = [
  { label: "Searching medical documents...", icon: Search },
  { label: "Reading blood reports & clinical notes...", icon: FileText },
  { label: "Comparing laboratory values against reference ranges...", icon: Scale },
  { label: "Synthesizing grounded response...", icon: Sparkles },
] as const;

export function ThinkingStateProgress() {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % THINKING_STEPS.length);
    }, 1600);
    return () => clearInterval(timer);
  }, []);

  const step = THINKING_STEPS[currentStepIndex];
  const StepIcon = step.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-3"
    >
      <div className="relative mt-1 flex size-9 shrink-0 items-center justify-center rounded-xl bg-accent text-primary ring-1 ring-brand-accent/25 shadow-sm">
        <Bot className="size-4" />
        <span className="absolute -bottom-0.5 -right-0.5 flex size-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-accent opacity-75" />
          <span className="relative inline-flex size-2.5 rounded-full bg-brand-accent" />
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-2 rounded-2xl rounded-bl-md border border-border/70 bg-card p-4 shadow-tinted">
        <div className="flex items-center gap-2 text-xs font-semibold text-primary">
          <Loader2 className="size-3.5 animate-spin text-brand-accent" />
          <span>MedVault Copilot is thinking</span>
        </div>

        <div className="h-6 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStepIndex}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2 text-sm text-foreground/90 font-medium"
            >
              <StepIcon className="size-4 shrink-0 text-muted-foreground" />
              <span>{step.label}</span>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Pulsing indicator dots */}
        <div className="flex items-center gap-1 pt-1">
          {THINKING_STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`h-1 rounded-full transition-all duration-300 ${
                idx === currentStepIndex
                  ? "w-6 bg-brand-accent"
                  : "w-2 bg-muted-foreground/20"
              }`}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}
