import type { DocumentStatus } from "@/types/api";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatDocumentStatus } from "@/lib/format";

const STATUS_STYLES: Record<DocumentStatus, string> = {
  pending: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  uploaded: "bg-purple-500/10 text-purple-700 dark:text-purple-400",
  queued: "bg-indigo-500/10 text-indigo-700 dark:text-indigo-400",
  processing: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  ready: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  indexing: "bg-cyan-500/10 text-cyan-700 dark:text-cyan-400",
  indexed: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  completed: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  failed: "bg-destructive/10 text-destructive",
  rejected: "bg-orange-500/10 text-orange-700 dark:text-orange-400",
};

type DocumentStatusBadgeProps = {
  status: DocumentStatus;
  className?: string;
};

export function DocumentStatusBadge({ status, className }: DocumentStatusBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn("font-medium", STATUS_STYLES[status], className)}
    >
      {formatDocumentStatus(status)}
    </Badge>
  );
}
