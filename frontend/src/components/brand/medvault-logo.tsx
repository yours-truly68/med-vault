import Link from "next/link";

import { cn } from "@/lib/utils";

type MedVaultLogoProps = {
  href?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  /** Accepted for API compatibility with next/image logo variants. */
  priority?: boolean;
  /** Wordmark is always shown; kept for call-site compatibility. */
  showWordmark?: boolean;
};

const SIZE = {
  sm: { mark: "size-7 text-[0.7rem]", word: "text-sm" },
  md: { mark: "size-8 text-xs", word: "text-[0.9375rem]" },
  lg: { mark: "size-10 text-sm", word: "text-base" },
} as const;

export function MedVaultLogo({
  href = "/",
  className,
  size = "md",
  priority: _priority = false,
  showWordmark: _showWordmark = true,
}: MedVaultLogoProps) {
  const s = SIZE[size];

  const content = (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "brand-logo-mark inline-flex items-center justify-center rounded-md font-semibold tracking-tight",
          s.mark,
        )}
        aria-hidden
      >
        +
      </span>
      <span
        className={cn(
          "font-heading font-semibold tracking-[-0.02em] text-white",
          s.word,
        )}
      >
        MedVault
      </span>
    </span>
  );

  if (href) {
    return (
      <Link
        href={href}
        className="rounded-md outline-none transition-opacity hover:opacity-90 focus-visible:ring-2 focus-visible:ring-[var(--landing-accent,var(--auth-accent,#5eead4))] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--landing-bg,var(--auth-bg,#0a0f1a))]"
      >
        {content}
      </Link>
    );
  }

  return content;
}
