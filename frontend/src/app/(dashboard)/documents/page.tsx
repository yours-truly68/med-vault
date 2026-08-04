import type { Metadata } from "next";

import { DocumentsPageContent } from "@/components/features/documents/documents-page";

export const metadata: Metadata = {
  title: "Documents",
};

export default function DocumentsPage() {
  return <DocumentsPageContent />;
}
