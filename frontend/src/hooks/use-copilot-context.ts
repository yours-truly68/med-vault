"use client";

import { usePathname } from "next/navigation";
import { useUiStore } from "@/stores/ui-store";

export type CopilotContextInfo = {
  pathname: string;
  pageTitle: string;
  contextDescription: string;
  documentId: string | null;
  selectedFamilyMemberId: string | null;
  suggestedPrompts: string[];
};

export function useCopilotContext(): CopilotContextInfo {
  const pathname = usePathname();
  const selectedFamilyMemberId = useUiStore((state) => state.selectedFamilyMemberId);

  // Extract document ID if on /documents/[id]
  const docMatch = pathname.match(/^\/documents\/([a-f0-9-]+)$/i);
  const documentId = docMatch ? docMatch[1] : null;

  let pageTitle = "MedVault App";
  let contextDescription = "General medical vault context";
  let suggestedPrompts: string[] = [
    "What are my latest blood report results?",
    "List all my prescribed medications.",
    "Were any lab values outside reference ranges?",
    "How do I upload new medical documents?",
  ];

  if (pathname === "/dashboard") {
    pageTitle = "Dashboard";
    contextDescription = "Overview of medical records and recent document uploads";
    suggestedPrompts = [
      "Summarize recent activity across all documents.",
      "Show abnormal lab values from recent reports.",
      "List current medications and dosages.",
      "What documents require my attention?",
    ];
  } else if (pathname === "/timeline") {
    pageTitle = "Medical Timeline";
    contextDescription = "Chronological history of medical visits, lab tests, and procedures";
    suggestedPrompts = [
      "Explain the latest events in my timeline.",
      "Are there any gaps in my medical history?",
      "Show all lab test events from 2026.",
      "Summarize my hospital visit history.",
    ];
  } else if (pathname.startsWith("/documents")) {
    if (documentId) {
      pageTitle = "Document Details";
      contextDescription = `Viewing document ${documentId.slice(0, 8)}`;
      suggestedPrompts = [
        "Summarize this document.",
        "List all lab measurements in this report.",
        "Compare this report with previous tests.",
        "Explain key diagnoses found in this file.",
      ];
    } else {
      pageTitle = "Document Vault";
      contextDescription = "Browsing uploaded prescriptions, lab reports, and summaries";
      suggestedPrompts = [
        "Which lab reports have abnormal results?",
        "Find prescriptions issued in the last 30 days.",
        "How many documents are currently READY?",
        "What does INDEXED status mean?",
      ];
    }
  } else if (pathname === "/upload") {
    pageTitle = "Document Upload";
    contextDescription = "Uploading new medical files to vault";
    suggestedPrompts = [
      "How does document processing work?",
      "What file formats are supported?",
      "What is the difference between READY and INDEXED?",
      "How are family members assigned to files?",
    ];
  } else if (pathname === "/family-members") {
    pageTitle = "Family Members";
    contextDescription = "Managing family profiles and records segregation";
    suggestedPrompts = [
      "How do Family Members work in MedVault?",
      "How do I filter documents by family member?",
      "Can I switch profiles while asking questions?",
    ];
  } else if (pathname === "/settings") {
    pageTitle = "Settings";
    contextDescription = "System configuration, AI models, and preferences";
    suggestedPrompts = [
      "What AI provider is configured for chat?",
      "How does RAG vector search work?",
      "Where is my medical data stored?",
    ];
  }

  return {
    pathname,
    pageTitle,
    contextDescription,
    documentId,
    selectedFamilyMemberId,
    suggestedPrompts,
  };
}
