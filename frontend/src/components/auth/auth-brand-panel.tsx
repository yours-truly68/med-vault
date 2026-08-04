import Image from "next/image";
import {
  Check,
  FolderUp,
  Lock,
  MessageSquareText,
  Search,
  Shield,
} from "lucide-react";

import { MedVaultLogo } from "@/components/brand";

const FEATURES = [
  {
    icon: FolderUp,
    title: "Upload & Organize",
    description:
      "Drop prescriptions, labs, and bills. MedVault classifies and files them for you.",
  },
  {
    icon: Search,
    title: "Smart Search & Timeline",
    description:
      "Find a result by name, month, or date across your family's records.",
  },
  {
    icon: MessageSquareText,
    title: "AI Health Assistant",
    description:
      "Ask grounded questions about uploaded documents, with citations you can open.",
  },
] as const;

const TRUST = [
  { icon: Lock, label: "Encrypted in transit" },
  { icon: Shield, label: "Private by design" },
  { icon: Check, label: "Yours to control" },
] as const;

export function AuthBrandPanel() {
  return (
    <aside className="auth-brand relative hidden overflow-hidden lg:flex lg:flex-col">
      <div className="auth-brand-glow" aria-hidden />
      <Image
        src="/brand/auth-glow-plate.png"
        alt=""
        width={1024}
        height={1024}
        priority
        className="pointer-events-none absolute top-1/2 right-[-12%] size-[min(72vh,560px)] -translate-y-1/2 object-contain opacity-55 mix-blend-screen"
      />

      <div className="relative z-10 flex h-full flex-col p-10 xl:p-12">
        <MedVaultLogo
          href="/"
          size="md"
          priority
          className="[&_span]:text-white"
        />

        <div className="mt-10 flex flex-1 flex-col justify-center gap-10 xl:mt-12">
          <div className="max-w-lg space-y-5">
            <p className="auth-badge inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium">
              <Check className="size-3.5 shrink-0" aria-hidden />
              Secure. Private. Always yours.
            </p>

            <h1 className="font-heading text-[2.35rem] leading-[1.12] font-semibold tracking-[-0.03em] text-white text-balance xl:text-[2.75rem]">
              Your health.{" "}
              <span className="auth-accent-text">Organized for life.</span>
            </h1>

            <p className="max-w-[42ch] text-[0.975rem] leading-relaxed text-white/65 text-pretty">
              Store, organize, and understand your family&apos;s medical records
              in one secure vault.
            </p>
          </div>

          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,0.95fr)] items-center gap-6 xl:gap-8">
            <ul className="space-y-5">
              {FEATURES.map(({ icon: Icon, title, description }) => (
                <li key={title} className="flex gap-3.5">
                  <span className="auth-feature-icon flex size-10 shrink-0 items-center justify-center rounded-lg">
                    <Icon className="size-4" aria-hidden />
                  </span>
                  <div className="min-w-0 space-y-1">
                    <p className="text-sm font-semibold tracking-tight text-white">
                      {title}
                    </p>
                    <p className="text-[0.8125rem] leading-relaxed text-white/55 text-pretty">
                      {description}
                    </p>
                  </div>
                </li>
              ))}
            </ul>

            <div className="auth-hero-asset relative mx-auto aspect-square w-full max-w-[340px]">
              <Image
                src="/brand/auth-vault-folder.png"
                alt=""
                fill
                priority
                sizes="(min-width: 1280px) 340px, 280px"
                className="object-contain drop-shadow-[0_24px_60px_rgba(0,0,0,0.55)]"
              />
            </div>
          </div>
        </div>

        <ul className="relative z-10 mt-10 flex flex-wrap gap-x-6 gap-y-3 border-t border-white/10 pt-6">
          {TRUST.map(({ icon: Icon, label }) => (
            <li
              key={label}
              className="flex items-center gap-2 text-xs text-white/50"
            >
              <Icon className="size-3.5 shrink-0 text-[var(--auth-accent)]" aria-hidden />
              {label}
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
