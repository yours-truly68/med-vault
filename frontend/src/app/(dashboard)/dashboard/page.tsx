import type { Metadata } from "next";

import { DashboardPageContent } from "@/components/features/dashboard/dashboard-page";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default function DashboardPage() {
  return <DashboardPageContent />;
}
