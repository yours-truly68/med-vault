"use client";

import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { toast } from "sonner";
import { useUiStore } from "@/stores/ui-store";

export type CopilotToolAction =
  | { type: "navigate"; path: string; label: string }
  | { type: "open_report"; documentId: string; label: string }
  | { type: "filter_family_member"; familyMemberId: string; label: string }
  | { type: "compare_reports"; label: string }
  | { type: "view_medications"; label: string }
  | { type: "show_timeline"; label: string };

export function parseToolActionsFromResponse(text: string): CopilotToolAction[] {
  const actions: CopilotToolAction[] = [];
  const lower = text.toLowerCase();

  // Detect navigation intents
  if (lower.includes("timeline") || lower.includes("chronological")) {
    actions.push({
      type: "show_timeline",
      label: "Show Timeline",
    });
  }

  if (lower.includes("upload") || lower.includes("add file")) {
    actions.push({
      type: "navigate",
      path: "/upload",
      label: "Go to Upload",
    });
  }

  if (lower.includes("medication") || lower.includes("prescrib")) {
    actions.push({
      type: "view_medications",
      label: "View Medications",
    });
  }

  if (lower.includes("compare") || lower.includes("previous report")) {
    actions.push({
      type: "compare_reports",
      label: "Compare Reports",
    });
  }

  if (lower.includes("vault") || lower.includes("all documents")) {
    actions.push({
      type: "navigate",
      path: "/documents",
      label: "View Vault",
    });
  }

  // Extract document ID if mentioned
  const docMatch = text.match(/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/i);
  if (docMatch) {
    actions.push({
      type: "open_report",
      documentId: docMatch[1],
      label: "Open Report",
    });
  }

  return actions;
}

export function executeCopilotToolAction(
  action: CopilotToolAction,
  router: AppRouterInstance
) {
  switch (action.type) {
    case "navigate":
      router.push(action.path);
      toast.success(`Navigating to ${action.label}`);
      break;

    case "open_report":
      router.push(`/documents/${action.documentId}`);
      toast.success("Opening report details");
      break;

    case "show_timeline":
      router.push("/timeline");
      toast.success("Opening Medical Timeline");
      break;

    case "view_medications":
      router.push("/documents");
      toast.success("Filtering documents for medications");
      break;

    case "compare_reports":
      router.push("/timeline");
      toast.info("Comparing reports in timeline");
      break;

    case "filter_family_member":
      useUiStore.getState().setSelectedFamilyMemberId(action.familyMemberId);
      toast.success("Family member filter applied");
      break;
  }
}
