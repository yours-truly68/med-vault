"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Upload, Clock, Sparkles, Scale, UserPlus, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "@/stores/copilot-store";

export function QuickActionsBar() {
  const toggleCopilot = useCopilotStore((state) => state.toggleCopilot);

  const actions = [
    {
      label: "Upload Report",
      href: "/upload",
      icon: Upload,
      color: "bg-primary text-primary-foreground hover:bg-primary/90",
    },
    {
      label: "Open Timeline",
      href: "/timeline",
      icon: Clock,
      color: "bg-card border border-border/70 text-foreground hover:border-brand-accent/40 hover:bg-accent/40",
    },
    {
      label: "Ask Copilot",
      onClick: toggleCopilot,
      icon: Sparkles,
      color: "bg-accent text-primary border border-brand-accent/30 hover:bg-accent/80",
    },
    {
      label: "Compare Reports",
      href: "/timeline",
      icon: Scale,
      color: "bg-card border border-border/70 text-foreground hover:border-brand-accent/40 hover:bg-accent/40",
    },
    {
      label: "Add Family Member",
      href: "/family-members",
      icon: UserPlus,
      color: "bg-card border border-border/70 text-foreground hover:border-brand-accent/40 hover:bg-accent/40",
    },
  ];

  return (
    <div className="space-y-2">
      <h2 className="font-heading text-xs font-bold uppercase tracking-wider text-muted-foreground">
        Quick Actions
      </h2>
      <div className="flex flex-wrap gap-2.5">
        {actions.map((act, idx) => {
          const Icon = act.icon;
          if (act.onClick) {
            return (
              <motion.button
                key={act.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.15, delay: idx * 0.03 }}
                type="button"
                onClick={act.onClick}
                className={`inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold shadow-xs transition-all ${act.color}`}
              >
                <Icon className="size-3.5 text-brand-accent animate-pulse" />
                <span>{act.label}</span>
              </motion.button>
            );
          }

          return (
            <motion.div
              key={act.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.15, delay: idx * 0.03 }}
            >
              <Button asChild size="sm" className={`rounded-xl text-xs font-bold h-9 gap-2 shadow-xs ${act.color}`}>
                <Link href={act.href}>
                  <Icon className="size-3.5" />
                  <span>{act.label}</span>
                </Link>
              </Button>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
