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

      <div className="relative z-10 flex h-full flex-col p-9 xl:p-11">
        <MedVaultLogo
          href="/"
          size="md"
          priority
          className="[&_span]:text-white"
        />

        <div className="mt-8 flex flex-1 flex-col justify-center gap-8 xl:mt-10 xl:gap-9">
          <div className="max-w-md space-y-4">
            <p className="auth-badge inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-[0.6875rem] font-medium tracking-wide">
              <Check className="size-3.5 shrink-0" aria-hidden />
              Secure. Private. Always yours.
            </p>

            <h1 className="font-heading text-[1.75rem] leading-[1.2] font-semibold tracking-[-0.025em] text-white text-balance xl:text-[2rem]">
              Your health.{" "}
              <span className="auth-accent-text">Organized for life.</span>
            </h1>

            <p className="max-w-[40ch] text-sm leading-relaxed text-white/65 text-pretty">
              Store, organize, and understand your family&apos;s medical records
              in one secure vault.
            </p>
          </div>

          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,0.85fr)] items-center gap-5 xl:gap-7">
            <ul className="space-y-4">
              {FEATURES.map(({ icon: Icon, title, description }) => (
                <li key={title} className="flex gap-3">
                  <span className="auth-feature-icon flex size-9 shrink-0 items-center justify-center rounded-lg">
                    <Icon className="size-3.5" aria-hidden />
                  </span>
                  <div className="min-w-0 space-y-0.5">
                    <p className="text-[0.8125rem] font-semibold tracking-tight text-white">
                      {title}
                    </p>
                    <p className="text-xs leading-relaxed text-white/55 text-pretty">
                      {description}
                    </p>
                  </div>
                </li>
              ))}
            </ul>

            <div className="auth-hero-asset relative mx-auto aspect-square w-full max-w-[280px] xl:max-w-[300px]">
              <Image
                src="/brand/auth-vault-folder.png"
                alt=""
                fill
                priority
                sizes="(min-width: 1280px) 300px, 260px"
                className="object-contain drop-shadow-[0_24px_60px_rgba(0,0,0,0.55)]"
              />
            </div>
          </div>
        </div>

        <ul className="relative z-10 mt-8 flex flex-wrap gap-x-5 gap-y-2 border-t border-white/10 pt-5">
          {TRUST.map(({ icon: Icon, label }) => (
            <li
              key={label}
              className="flex items-center gap-2 text-[0.6875rem] text-white/50"
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
