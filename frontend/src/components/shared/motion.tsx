import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PageMotionProps = {
  children: ReactNode;
  className?: string;
};

export function PageMotion({ children, className }: PageMotionProps) {
  return <div className={cn("page-enter", className)}>{children}</div>;
}

type StaggerMotionProps = {
  children: ReactNode;
  index?: number;
  className?: string;
};

export function StaggerMotion({
  children,
  index = 0,
  className,
}: StaggerMotionProps) {
  const staggerClass =
    index === 0
      ? "stagger-1"
      : index === 1
        ? "stagger-2"
        : index === 2
          ? "stagger-3"
          : "stagger-4";

  return (
    <div className={cn("page-enter", staggerClass, className)}>{children}</div>
  );
}
