"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, CheckCircle2, Activity } from "lucide-react";
import type { SupportingLabValue } from "@/types/api";
import { cn } from "@/lib/utils";

type LabValueCardProps = {
  item: SupportingLabValue | string;
  index: number;
};

export function determineLabStatus(item: SupportingLabValue | string): {
  status: "high" | "low" | "normal" | "unknown";
  label: string;
  badgeClass: string;
  icon: any;
} {
  if (typeof item === "string") {
    const lower = item.toLowerCase();
    if (lower.includes("high") || lower.includes("above") || lower.includes("elevated")) {
      return {
        status: "high",
        label: "Above Range",
        badgeClass: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
        icon: TrendingUp,
      };
    }
    if (lower.includes("low") || lower.includes("below") || lower.includes("deficient")) {
      return {
        status: "low",
        label: "Below Range",
        badgeClass: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
        icon: TrendingDown,
      };
    }
    return {
      status: "unknown",
      label: "Lab Value",
      badgeClass: "bg-muted text-muted-foreground border-border/60",
      icon: Activity,
    };
  }

  const numVal = typeof item.value === "number" ? item.value : item.value ? parseFloat(String(item.value)) : NaN;
  const refLow = typeof item.reference_low === "number" ? item.reference_low : item.reference_low ? parseFloat(String(item.reference_low)) : NaN;
  const refHigh = typeof item.reference_high === "number" ? item.reference_high : item.reference_high ? parseFloat(String(item.reference_high)) : NaN;

  if (!isNaN(numVal)) {
    if (!isNaN(refHigh) && numVal > refHigh) {
      return {
        status: "high",
        label: "Above Range",
        badgeClass: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
        icon: TrendingUp,
      };
    }
    if (!isNaN(refLow) && numVal < refLow) {
      return {
        status: "low",
        label: "Below Range",
        badgeClass: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
        icon: TrendingDown,
      };
    }
    if (!isNaN(refLow) || !isNaN(refHigh)) {
      return {
        status: "normal",
        label: "Normal Range",
        badgeClass: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
        icon: CheckCircle2,
      };
    }
  }

  return {
    status: "unknown",
    label: "Measured",
    badgeClass: "bg-muted/60 text-foreground/80 border-border/60",
    icon: Activity,
  };
}

export function LabValueCard({ item, index }: LabValueCardProps) {
  const isString = typeof item === "string";
  const testName = isString ? item : item.test_name || "Lab Value";
  const val = isString ? null : item.value;
  const unit = isString ? null : item.unit;
  const refLow = isString ? null : item.reference_low;
  const refHigh = isString ? null : item.reference_high;

  const { label, badgeClass, icon: Icon } = determineLabStatus(item);

  let refText = "";
  if (refLow !== null && refHigh !== null) {
    refText = `Ref: ${refLow} - ${refHigh}`;
  } else if (refHigh !== null) {
    refText = `Ref < ${refHigh}`;
  } else if (refLow !== null) {
    refText = `Ref > ${refLow}`;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.04 }}
      className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-border/70 bg-card/90 p-3.5 shadow-sm transition-all hover:border-brand-accent/40 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="line-clamp-1 text-xs font-semibold tracking-tight text-muted-foreground">
          {testName}
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[0.6875rem] font-medium transition-colors",
            badgeClass
          )}
        >
          <Icon className="size-3 shrink-0" />
          {label}
        </span>
      </div>

      <div className="mt-2.5 flex items-baseline gap-1.5">
        {val !== null ? (
          <>
            <span className="font-heading text-xl font-bold tracking-tight text-foreground">
              {val}
            </span>
            {unit ? (
              <span className="text-xs font-medium text-muted-foreground">{unit}</span>
            ) : null}
          </>
        ) : (
          <span className="text-sm font-medium text-foreground">{testName}</span>
        )}
      </div>

      {refText ? (
        <div className="mt-2 border-t border-border/40 pt-1.5 text-[0.6875rem] font-medium text-muted-foreground">
          {refText}
        </div>
      ) : null}
    </motion.div>
  );
}

export function StructuredLabValuesGrid({
  items,
}: {
  items: (SupportingLabValue | string)[];
}) {
  if (!items || items.length === 0) return null;

  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-1.5">
        <Activity className="size-3.5 text-brand-accent" />
        <span className="text-xs font-semibold text-muted-foreground">
          Laboratory measurements ({items.length})
        </span>
      </div>
      <div className="grid gap-2.5 sm:grid-cols-2">
        {items.map((item, idx) => (
          <LabValueCard key={idx} item={item} index={idx} />
        ))}
      </div>
    </div>
  );
}
