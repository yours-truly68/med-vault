import type { DocumentType } from "@/types/api";

import { Badge } from "@/components/ui/badge";
import { formatDocumentType } from "@/lib/format";

type DocumentTypeBadgeProps = {
  type: DocumentType | null | undefined;
};

export function DocumentTypeBadge({ type }: DocumentTypeBadgeProps) {
  return (
    <Badge variant="outline" className="font-normal">
      {formatDocumentType(type)}
    </Badge>
  );
}
