"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Clock, FileText, Upload, Users, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function detectNavigationRecommendation(text: string): {
  label: string;
  href: string;
  icon: any;
} | null {
  const lower = text.toLowerCase();

  if (lower.includes("timeline") || lower.includes("chronological")) {
    return { label: "Open Timeline", href: "/timeline", icon: Clock };
  }
  if (lower.includes("upload") || lower.includes("add document")) {
    return { label: "Go to Upload", href: "/upload", icon: Upload };
  }
  if (lower.includes("documents") || lower.includes("vault")) {
    return { label: "View Documents Vault", href: "/documents", icon: FileText };
  }
  if (lower.includes("family member") || lower.includes("patient profile")) {
    return { label: "Manage Family Members", href: "/family-members", icon: Users };
  }
  if (lower.includes("dashboard") || lower.includes("overview")) {
    return { label: "View Dashboard", href: "/dashboard", icon: BarChart3 };
  }

  return null;
}

export function SuggestedNavigationAction({
  content,
  onNavigate,
}: {
  content: string;
  onNavigate?: () => void;
}) {
  const router = useRouter();
  const rec = detectNavigationRecommendation(content);

  if (!rec) return null;

  const Icon = rec.icon;

  const handleClick = () => {
    router.push(rec.href);
    if (onNavigate) onNavigate();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15, delay: 0.2 }}
      className="mt-2.5 pt-2 border-t border-border/40 flex items-center justify-between gap-2"
    >
      <span className="text-[0.6875rem] font-medium text-muted-foreground">
        Recommended Surface
      </span>
      <Button
        type="button"
        size="sm"
        variant="outline"
        onClick={handleClick}
        className="rounded-xl text-xs gap-1.5 h-7 bg-accent/30 hover:bg-accent hover:text-primary border-brand-accent/30"
      >
        <Icon className="size-3 text-brand-accent" />
        <span>{rec.label}</span>
        <ArrowRight className="size-3" />
      </Button>
    </motion.div>
  );
}
