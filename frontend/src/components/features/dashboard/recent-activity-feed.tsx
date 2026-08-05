"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Activity, ArrowRight, FileText, Clock } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useTimelineEvents } from "@/hooks/use-timeline";
import { useUiStore } from "@/stores/ui-store";
import { formatDate } from "@/lib/format";

export function RecentActivityFeed() {
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);
  const timelineQuery = useTimelineEvents({
    family_member_id: selectedFamilyMemberId,
    limit: 8,
  });

  if (timelineQuery.isPending && timelineQuery.fetchStatus === "fetching" && !timelineQuery.data) {
    return <Skeleton className="h-64 w-full rounded-2xl" />;
  }

  if (timelineQuery.isError) {
    return (
      <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-xs text-destructive">
        Unable to load recent activity feed.
      </div>
    );
  }

  const events = timelineQuery.data?.items ?? [];

  if (events.length === 0) {
    return (
      <div className="rounded-2xl border border-border/70 bg-card p-5 text-center text-xs text-muted-foreground">
        No recent health activity recorded yet.
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: 0.15 }}
      className="rounded-2xl border border-border/70 bg-card p-5 shadow-tinted space-y-4"
    >
      <div className="flex items-center justify-between border-b border-border/50 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-accent text-primary">
            <Activity className="size-4 text-brand-accent" />
          </div>
          <h2 className="font-heading text-base font-bold tracking-tight text-foreground">
            Recent Health Activity
          </h2>
        </div>
        <Link
          href="/timeline"
          className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
        >
          <span>Open Timeline</span>
          <ArrowRight className="size-3.5" />
        </Link>
      </div>

      <div className="space-y-2.5">
        {events.slice(0, 5).map((evt) => (
          <Link
            key={evt.id}
            href={evt.document_id ? `/documents/${evt.document_id}` : "/timeline"}
            className="group flex items-start justify-between gap-3 rounded-xl border border-border/60 bg-muted/20 p-3 transition-colors hover:border-brand-accent/40 hover:bg-accent/40"
          >
            <div className="flex items-start gap-2.5 min-w-0">
              <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-card text-muted-foreground group-hover:text-primary ring-1 ring-border/50">
                <FileText className="size-3.5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-foreground group-hover:text-primary truncate capitalize">
                  {evt.title}
                </p>
                {evt.description ? (
                  <p className="text-[0.6875rem] text-muted-foreground line-clamp-1 mt-0.5">
                    {evt.description}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="flex items-center gap-1 text-[0.6875rem] font-semibold text-muted-foreground shrink-0">
              <Clock className="size-3" />
              <span>{formatDate(evt.event_date)}</span>
            </div>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
