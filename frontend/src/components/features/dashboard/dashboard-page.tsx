"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Upload, Sparkles, ArrowRight, ShieldCheck } from "lucide-react";

import { PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { useUiStore } from "@/stores/ui-store";
import { useCopilotStore } from "@/stores/copilot-store";

import { FamilyOverviewGrid } from "./family-overview-grid";
import { QuickActionsBar } from "./quick-actions-bar";
import { ClinicalSnapshotCard } from "./clinical-snapshot-card";
import { RecentActivityFeed } from "./recent-activity-feed";
import { HealthTrendsPreview } from "./health-trends-preview";
import { RecentDocumentsGrid } from "./recent-documents-grid";

export function DashboardPageContent() {
  const documentsQuery = useDocuments();
  const familyMembersQuery = useFamilyMembers();
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);
  const toggleCopilot = useCopilotStore((state) => state.toggleCopilot);

  const familyMembers = familyMembersQuery.data?.items ?? [];
  const documents = documentsQuery.data?.items ?? [];
  const trendsMemberId = selectedFamilyMemberId ?? familyMembers[0]?.id ?? null;

  const isVaultEmpty = !documentsQuery.isLoading && documents.length === 0;

  return (
    <div className="space-y-6 pb-6">
      {/* Header Banner */}
      <PageHeader
        className="mb-0 border-b-0 pb-0"
        title="Medical Control Center"
        description="Who needs attention · What changed recently · Clinical insights · Next actions"
        actions={
          <div className="flex items-center gap-2">
            <Button
              type="button"
              onClick={toggleCopilot}
              className="rounded-xl text-xs font-bold gap-1.5 bg-accent text-primary border border-brand-accent/30 hover:bg-accent/80"
            >
              <Sparkles className="size-3.5 text-brand-accent animate-pulse" />
              <span>Ask Copilot</span>
            </Button>

            <Button asChild className="rounded-xl text-xs font-bold gap-1.5">
              <Link href="/upload">
                <Upload className="size-3.5" />
                <span>Upload Report</span>
              </Link>
            </Button>
          </div>
        }
      />

      {/* Quick Action Shortcuts */}
      <QuickActionsBar />

      {/* Primary Section: Family Overview (Loads Independently) */}
      <FamilyOverviewGrid />

      {/* Vault Empty Onboarding State vs Independent Widgets */}
      {isVaultEmpty ? (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="rounded-2xl border border-border/80 bg-gradient-to-b from-card via-background to-muted/20 p-8 text-center space-y-4 shadow-tinted max-w-3xl mx-auto my-6"
        >
          <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-accent text-primary ring-1 ring-brand-accent/30 shadow-md">
            <ShieldCheck className="size-7 text-brand-accent animate-pulse" />
          </div>
          <h2 className="font-heading text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Welcome to Your Family Medical Control Center
          </h2>
          <p className="mx-auto max-w-md text-xs leading-relaxed text-muted-foreground sm:text-sm">
            Upload blood reports, prescriptions, or discharge summaries to instantly unlock clinical range tracking, automated timeline event generation, and grounded AI copilot answers.
          </p>
          <Button asChild size="lg" className="rounded-xl font-bold gap-2">
            <Link href="/upload">
              <Upload className="size-4" />
              <span>Upload Your First Medical Report</span>
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </motion.div>
      ) : (
        <>
          {/* Clinical Health Snapshot & Recent Activity Feed (Load Independently) */}
          <div className="grid gap-5 lg:grid-cols-2">
            <ClinicalSnapshotCard />
            <RecentActivityFeed />
          </div>

          {/* Laboratory Trends Preview (Loads Independently) */}
          <HealthTrendsPreview familyMemberId={trendsMemberId} />

          {/* Recent Documents Grid (Loads Independently) */}
          <RecentDocumentsGrid />
        </>
      )}
    </div>
  );
}
