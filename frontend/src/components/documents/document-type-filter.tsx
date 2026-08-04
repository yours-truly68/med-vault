"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatDocumentType } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { DocumentType } from "@/types/api";

const DOCUMENT_TYPES: DocumentType[] = [
  "prescription",
  "lab_report",
  "hospital_bill",
  "pharmacy_bill",
  "discharge_summary",
  "imaging_report",
  "other",
  "unrelated",
];

type DocumentTypeFilterProps = {
  value: DocumentType | null;
  onChange: (value: DocumentType | null) => void;
  className?: string;
};

export function DocumentTypeFilter({
  value,
  onChange,
  className,
}: DocumentTypeFilterProps) {
  return (
    <Select
      value={value ?? "all"}
      onValueChange={(next) => {
        onChange(next === "all" ? null : (next as DocumentType));
      }}
    >
      <SelectTrigger className={cn("w-full sm:w-52", className)} aria-label="Filter by type">
        <SelectValue placeholder="All types" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All types</SelectItem>
        {DOCUMENT_TYPES.map((type) => (
          <SelectItem key={type} value={type}>
            {formatDocumentType(type)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
