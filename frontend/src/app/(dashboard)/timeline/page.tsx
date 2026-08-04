import type { Metadata } from "next";

import { TimelinePageContent } from "@/components/features/timeline/timeline-page";

export const metadata: Metadata = {
  title: "Timeline",
};

export default function TimelinePage() {
  return <TimelinePageContent />;
}
