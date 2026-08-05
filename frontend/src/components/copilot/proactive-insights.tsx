"use client";

import { motion } from "framer-motion";
import { Sparkles, AlertTriangle, Layers, Clock, Pill } from "lucide-react";
import type { ChatAskResponse } from "@/types/api";
import { determineLabStatus } from "@/components/features/chat/lab-values-grid";

export function generateProactiveInsights(
  response?: ChatAskResponse
): { label: string; icon: any; color: string }[] {
  if (!response) return [];

  const insights: { label: string; icon: any; color: string }[] = [];
  const details = response.supporting_details;

  // Check for lab range highlights
  if (details?.lab_values) {
    const abnormal = details.lab_values.filter((item) => {
      const { status } = determineLabStatus(item);
      return status === "high" || status === "low";
    });

    if (abnormal.length > 0) {
      insights.push({
        label: `${abnormal.length} abnormal lab measurement${abnormal.length > 1 ? "s" : ""} detected in report context`,
        icon: AlertTriangle,
        color: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30",
      });
    }
  }

  // Citation document count
  if (response.citations && response.citations.length > 1) {
    insights.push({
      label: `Cross-referenced across ${response.citations.length} documents in your vault`,
      icon: Layers,
      color: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/30",
    });
  }

  // Medications found
  if (details?.medicines && details.medicines.length > 0) {
    insights.push({
      label: `Active prescription records found (${details.medicines.length} medications)`,
      icon: Pill,
      color: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
    });
  }

  // Timeline events found
  if (response.timeline && response.timeline.length > 0) {
    insights.push({
      label: `Medical timeline history available (${response.timeline.length} events)`,
      icon: Clock,
      color: "bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/30",
    });
  }

  return insights;
}

export function ProactiveInsightsBanner({
  response,
}: {
  response?: ChatAskResponse;
}) {
  const insights = generateProactiveInsights(response);

  if (insights.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-1.5 pt-1"
    >
      {insights.slice(0, 2).map((item, idx) => {
        const Icon = item.icon;
        return (
          <div
            key={idx}
            className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium ${item.color}`}
          >
            <Icon className="size-3.5 shrink-0" />
            <span className="truncate">{item.label}</span>
          </div>
        );
      })}
    </motion.div>
  );
}
