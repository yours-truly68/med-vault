import type { Metadata } from "next";

import { UploadPageContent } from "@/components/features/upload/upload-page";

export const metadata: Metadata = {
  title: "Upload",
};

export default function UploadPage() {
  return <UploadPageContent />;
}
