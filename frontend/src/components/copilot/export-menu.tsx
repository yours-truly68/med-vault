"use client";

import { useState } from "react";
import { Copy, Download, Printer, Check, Share2, MoreVertical } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import type { CopilotMessage } from "@/stores/copilot-store";

export function CopilotExportMenu({
  messages,
}: {
  messages: CopilotMessage[];
}) {
  const [copied, setCopied] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  if (!messages || messages.length === 0) return null;

  const handleCopyMarkdown = async () => {
    const text = messages
      .map(
        (m) =>
          `### ${m.role === "user" ? "User" : "MedVault Copilot"}\n\n${m.content}\n`
      )
      .join("\n---\n\n");

    await navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("Transcript copied to clipboard in Markdown");
    setTimeout(() => setCopied(false), 2000);
    setIsOpen(false);
  };

  const handleExportJson = () => {
    const dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(messages, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `medvault-chat-${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    toast.success("Exported conversation as JSON");
    setIsOpen(false);
  };

  const handlePrint = () => {
    window.print();
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <Button
        type="button"
        variant="ghost"
        size="icon-xs"
        title="Export options"
        onClick={() => setIsOpen(!isOpen)}
        className="rounded-lg text-muted-foreground hover:text-foreground"
      >
        <MoreVertical className="size-3.5" />
      </Button>

      {isOpen ? (
        <div className="absolute right-0 top-8 z-50 w-44 rounded-xl border border-border/80 bg-card p-1 shadow-lg space-y-0.5">
          <button
            type="button"
            onClick={handleCopyMarkdown}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-accent hover:text-primary transition-colors"
          >
            {copied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
            <span>Copy Transcript</span>
          </button>

          <button
            type="button"
            onClick={handleExportJson}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-accent hover:text-primary transition-colors"
          >
            <Download className="size-3.5" />
            <span>Export JSON Data</span>
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-accent hover:text-primary transition-colors"
          >
            <Printer className="size-3.5" />
            <span>Print / Save PDF</span>
          </button>
        </div>
      ) : null}
    </div>
  );
}
