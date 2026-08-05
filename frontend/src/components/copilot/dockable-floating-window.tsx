"use client";

import { useRef, useState, useEffect, type ReactNode, type MouseEvent as ReactMouseEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useCopilotStore, type DockCorner } from "@/stores/copilot-store";
import { cn } from "@/lib/utils";

type DockableFloatingWindowProps = {
  children: ReactNode;
};

const CORNER_POSITIONS: Record<
  DockCorner,
  { top?: string; bottom?: string; left?: string; right?: string }
> = {
  "top-left": { top: "1.25rem", left: "1.25rem" },
  "top-right": { top: "1.25rem", right: "1.25rem" },
  "bottom-left": { bottom: "1.25rem", left: "1.25rem" },
  "bottom-right": { bottom: "1.25rem", right: "1.25rem" },
};

export function DockableFloatingWindow({ children }: DockableFloatingWindowProps) {
  const { mode, dockCorner, setDockCorner } = useCopilotStore();

  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [dragPosition, setDragPosition] = useState<{ x: number; y: number } | null>(null);
  const [activePreviewCorner, setActivePreviewCorner] = useState<DockCorner | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Handle Drag ONLY when clicking the dedicated drag handle element
  const handleTitleDrag = (e: ReactMouseEvent) => {
    if (mode !== "expanded") return;
    const target = e.target as HTMLElement;

    // Strict safety check: Never drag if interacting with buttons, inputs, links, or text
    if (target.closest("button, input, textarea, a, kbd, svg, path")) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    setIsDragging(true);
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    setDragPosition({ x: rect.left, y: rect.top });
    e.preventDefault();
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX - dragOffset.x;
      const y = e.clientY - dragOffset.y;
      setDragPosition({ x, y });

      const midX = window.innerWidth / 2;
      const midY = window.innerHeight / 2;

      let targetCorner: DockCorner = "bottom-right";
      if (e.clientX < midX && e.clientY < midY) {
        targetCorner = "top-left";
      } else if (e.clientX >= midX && e.clientY < midY) {
        targetCorner = "top-right";
      } else if (e.clientX < midX && e.clientY >= midY) {
        targetCorner = "bottom-left";
      } else {
        targetCorner = "bottom-right";
      }

      setActivePreviewCorner(targetCorner);
    };

    const handleMouseUp = () => {
      if (activePreviewCorner) {
        setDockCorner(activePreviewCorner);
      }
      setIsDragging(false);
      setDragPosition(null);
      setActivePreviewCorner(null);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, dragOffset, activePreviewCorner, setDockCorner]);

  if (mode === "fullscreen") {
    return (
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 h-[min(820px,94dvh)] w-[min(1100px,94vw)] rounded-2xl border border-border/80 bg-card shadow-2xl overflow-hidden flex flex-col">
        {children}
      </div>
    );
  }

  if (mode === "docked") {
    return (
      <div className="fixed top-0 right-0 z-50 h-dvh w-[min(540px,100vw)] rounded-l-2xl border-l border-border/80 bg-card shadow-2xl overflow-hidden flex flex-col">
        {children}
      </div>
    );
  }

  const cornerStyle = CORNER_POSITIONS[dockCorner] || CORNER_POSITIONS["bottom-right"];

  return (
    <>
      {/* Visual Snap Indicator */}
      <AnimatePresence>
        {isDragging && activePreviewCorner ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            style={CORNER_POSITIONS[activePreviewCorner]}
            className="fixed z-40 h-[min(680px,calc(100dvh-2.5rem))] w-[min(580px,calc(100vw-2.5rem))] rounded-2xl border-2 border-dashed border-brand-accent bg-accent/15 pointer-events-none"
          />
        ) : null}
      </AnimatePresence>

      <motion.div
        ref={containerRef}
        layout
        transition={{ type: "spring", stiffness: 340, damping: 30 }}
        style={
          isDragging && dragPosition
            ? {
                position: "fixed",
                left: `${dragPosition.x}px`,
                top: `${dragPosition.y}px`,
                margin: 0,
              }
            : {
                position: "fixed",
                ...cornerStyle,
              }
        }
        className={cn(
          "z-50 flex flex-col overflow-hidden rounded-2xl border border-border/80 bg-card shadow-2xl",
          "h-[min(680px,calc(100dvh-2.5rem))] w-[min(580px,calc(100vw-2.5rem))]",
          isDragging && "shadow-brand-accent/20 shadow-2xl scale-[1.005]"
        )}
      >
        <div
          onMouseDown={handleTitleDrag}
          className="flex flex-col h-full overflow-hidden"
        >
          {children}
        </div>
      </motion.div>
    </>
  );
}
