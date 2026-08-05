"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useCopilotStore } from "@/stores/copilot-store";
import { CopilotWindow } from "./copilot-window";
import { DockableFloatingWindow } from "./dockable-floating-window";

export function MedVaultCopilotLauncher() {
  const { isOpen, mode, toggleCopilot, setIsOpen, setMode } = useCopilotStore();

  // Global Keyboard Shortcuts (⌘K / Ctrl+K to toggle, Esc to close/minimize)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        toggleCopilot();
      } else if (event.key === "Escape" && isOpen) {
        event.preventDefault();
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, setIsOpen, toggleCopilot]);

  return (
    <>
      {/* Floating Action Launcher Button (Bottom-Right) */}
      <AnimatePresence>
        {!isOpen || mode === "minimized" ? (
          <motion.button
            type="button"
            initial={{ scale: 0.8, opacity: 0, y: 12 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 12 }}
            transition={{ duration: 0.2 }}
            onClick={toggleCopilot}
            className="fixed bottom-5 right-5 z-40 flex items-center gap-2.5 rounded-full border border-brand-accent/40 bg-card/95 px-4 py-3 text-foreground shadow-xl backdrop-blur-md transition-all hover:scale-105 hover:border-brand-accent hover:shadow-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
          >
            <div className="relative flex size-6 items-center justify-center rounded-lg bg-accent text-primary">
              <Sparkles className="size-4 text-brand-accent animate-pulse" />
              <span className="absolute -top-1 -right-1 flex size-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-accent opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-brand-accent" />
              </span>
            </div>
            <span className="font-heading text-xs font-bold tracking-tight">
              Copilot
            </span>
            <kbd className="hidden rounded-md border border-border/80 bg-muted px-1.5 py-0.5 text-[0.625rem] font-semibold text-muted-foreground sm:inline-block">
              ⌘K
            </kbd>
          </motion.button>
        ) : null}
      </AnimatePresence>

      {/* Copilot Window Container (Expanded / Draggable / Docked / Fullscreen) */}
      <AnimatePresence>
        {isOpen && mode !== "minimized" ? (
          <>
            {mode === "fullscreen" ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setMode("expanded")}
                className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
              />
            ) : null}

            <DockableFloatingWindow>
              <CopilotWindow />
            </DockableFloatingWindow>
          </>
        ) : null}
      </AnimatePresence>
    </>
  );
}
