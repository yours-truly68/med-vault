import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type LoadingGridProps = {
  count?: number;
  className?: string;
};

export function LoadingGrid({ count = 3, className }: LoadingGridProps) {
  return (
    <div
      className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-3", className)}
      aria-busy="true"
      aria-label="Loading"
    >
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="h-28 animate-pulse rounded-lg bg-muted/60"
        />
      ))}
    </div>
  );
}

type EmptyStateProps = {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  className?: string;
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border/80 bg-muted/10 px-6 py-14 text-center",
        className,
      )}
    >
      {Icon ? (
        <span className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Icon className="size-6" aria-hidden />
        </span>
      ) : null}
      <div className="space-y-2">
        <h2 className="font-heading text-lg font-semibold tracking-tight">
          {title}
        </h2>
        {description ? (
          <p className="mx-auto max-w-md text-sm leading-relaxed text-muted-foreground text-pretty">
            {description}
          </p>
        ) : null}
      </div>
      {action || secondaryAction ? (
        <div className="flex flex-wrap items-center justify-center gap-2 pt-1">
          {action}
          {secondaryAction}
        </div>
      ) : null}
    </div>
  );
}

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-12 text-center">
      <p className="text-sm text-destructive">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="text-sm font-medium text-primary underline-offset-4 hover:underline"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}
