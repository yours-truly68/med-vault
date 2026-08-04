import type { Metadata } from "next";

import { DocumentDetailPageContent } from "@/components/features/documents/document-detail-page";

export const metadata: Metadata = {
  title: "Document",
};

type DocumentDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function DocumentDetailPage({
  params,
}: DocumentDetailPageProps) {
  const { id } = await params;
  return <DocumentDetailPageContent documentId={id} />;
}
