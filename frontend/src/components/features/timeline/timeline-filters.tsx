"use client";

import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export type TimelineFilterCategory =
  | "all"
  | "recent"
  | "lab_report"
  | "prescription"
  | "discharge_summary"
  | "hospital_bill"
  | "abnormal"
  | "completed";

const FILTER_CHIPS: { id: TimelineFilterCategory; label: string }[] = [
  { id: "all", label: "All Events" },
  { id: "recent", label: "Recent" },
  { id: "lab_report", label: "Lab Reports" },
  { id: "prescription", label: "Prescriptions" },
  { id: "abnormal", label: "Abnormal Labs ⚠️" },
  { id: "discharge_summary", label: "Discharge Summaries" },
  { id: "hospital_bill", label: "Hospital Bills" },
  { id: "completed", label: "Completed" },
];

export function TimelineFilters({
  searchQuery,
  onSearchChange,
  activeFilter,
  onFilterChange,
  totalCount,
}: {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeFilter: TimelineFilterCategory;
  onFilterChange: (cat: TimelineFilterCategory) => void;
  totalCount: number;
}) {
  return (
    <div className="space-y-3">
      {/* Universal Instant Search Input */}
      <div className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search by diagnosis, doctor, hospital, lab test (HbA1c, LDL), date (2026, July), patient..."
          className="pl-10 pr-9 text-xs sm:text-sm rounded-xl h-10 shadow-xs"
          aria-label="Search timeline events"
        />
        {searchQuery ? (
          <button
            type="button"
            onClick={() => onSearchChange("")}
            className="absolute top-1/2 right-3 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        ) : null}
      </div>

      {/* Filter Chips Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-3">
        <div className="flex flex-wrap items-center gap-1.5 overflow-x-auto py-1">
          {FILTER_CHIPS.map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={() => onFilterChange(chip.id)}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-bold transition-all duration-180 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                activeFilter === chip.id
                  ? "bg-primary text-primary-foreground shadow-xs scale-[1.02]"
                  : "bg-muted/60 text-muted-foreground hover:bg-accent hover:text-foreground border border-border/50"
              )}
            >
              {chip.label}
            </button>
          ))}
        </div>

        <span className="text-xs font-semibold text-muted-foreground shrink-0">
          {totalCount} event{totalCount === 1 ? "" : "s"}
        </span>
      </div>
    </div>
  );
}
