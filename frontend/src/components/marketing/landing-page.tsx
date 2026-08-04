"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowRight, Lock, ShieldCheck } from "lucide-react";

import { MedVaultLogo } from "@/components/brand";
import { cn } from "@/lib/utils";

const FEATURES = [
  {
    n: "01",
    title: "Upload & organize",
    description: "Upload any medical document and we'll keep it organized.",
  },
  {
    n: "02",
    title: "Search & understand",
    description: "Find what you need instantly with powerful search and AI.",
  },
  {
    n: "03",
    title: "Timeline & insights",
    description: "See your health history come together in a clear timeline.",
  },
] as const;

/**
 * Landing — typography-led Persuade surface.
 * Motion thesis: "organized" is the signature reveal; everything else supports arrival + invitation.
 */
export function LandingPage() {
  const stageRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduceMotion(media.matches);
    const onChange = () => setReduceMotion(media.matches);
    media.addEventListener("change", onChange);
    const id = window.requestAnimationFrame(() => setReady(true));
    return () => {
      media.removeEventListener("change", onChange);
      window.cancelAnimationFrame(id);
    };
  }, []);

  const onPointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (reduceMotion || !stageRef.current) return;
      const rect = stageRef.current.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;
      stageRef.current.style.setProperty("--spot-x", `${x}%`);
      stageRef.current.style.setProperty("--spot-y", `${y}%`);
    },
    [reduceMotion],
  );

  return (
    <div
      ref={stageRef}
      className={cn("landing-shell", ready && "is-ready")}
      onPointerMove={onPointerMove}
    >
      <div className="landing-spot" aria-hidden />
      <div className="landing-breathe" aria-hidden />

      <header className="landing-enter landing-enter-1 relative z-20 mx-auto flex w-full max-w-5xl items-center justify-between px-5 pt-6 sm:px-8 sm:pt-8">
        <MedVaultLogo size="md" />
        <nav className="flex items-center gap-2 sm:gap-3" aria-label="Account">
          <Link
            href="/login"
            className="rounded-lg px-3 py-2 text-sm text-white/65 transition-colors hover:text-white focus-visible:ring-2 focus-visible:ring-[var(--landing-accent)] focus-visible:outline-none"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="landing-btn-outline inline-flex h-9 items-center rounded-lg px-3.5 text-sm font-medium transition-[background-color,border-color,transform,box-shadow] duration-200 hover:bg-[var(--landing-accent)]/10 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[var(--landing-accent)] focus-visible:outline-none"
          >
            Get started
          </Link>
        </nav>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-5xl flex-1 flex-col px-5 sm:px-8">
        <section className="flex min-h-[min(72dvh,640px)] flex-col items-center justify-center py-16 text-center sm:py-20">
          <p className="landing-enter landing-enter-2 landing-badge mb-6 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium">
            <Lock className="size-3.5" aria-hidden />
            Secure. Private. Always yours.
          </p>

          <h1 className="landing-enter landing-enter-3 font-heading max-w-[16ch] text-[2.35rem] leading-[1.08] font-semibold tracking-[-0.035em] text-white text-balance sm:text-[3.15rem] md:text-[3.5rem]">
            Your family&apos;s medical records,{" "}
            <span className="landing-accent-word">organized</span> for life.
          </h1>

          <p className="landing-enter landing-enter-4 mt-5 max-w-[42ch] text-[0.975rem] leading-relaxed text-white/55 text-pretty sm:text-base">
            Store, organize, and understand prescriptions, labs, bills, and
            imaging - all in one secure place.
          </p>

          <div className="landing-enter landing-enter-5 mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/register"
              className="landing-btn-primary group inline-flex h-11 items-center gap-2 rounded-lg px-5 text-sm font-semibold text-[var(--landing-bg)] transition-[transform,box-shadow,filter] duration-200 hover:brightness-110 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[var(--landing-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--landing-bg)] focus-visible:outline-none"
            >
              Get started for free
              <ArrowRight
                className="size-4 transition-transform duration-200 group-hover:translate-x-0.5"
                aria-hidden
              />
            </Link>
            <Link
              href="/login"
              className="landing-btn-outline inline-flex h-11 items-center rounded-lg px-5 text-sm font-medium transition-[background-color,border-color,transform] duration-200 hover:bg-white/5 active:scale-[0.98] focus-visible:ring-2 focus-visible:ring-[var(--landing-accent)] focus-visible:outline-none"
            >
              Sign in
            </Link>
          </div>

          <p className="landing-enter landing-enter-6 mt-8 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs text-white/40">
            <ShieldCheck
              className="size-3.5 text-[var(--landing-accent)]"
              aria-hidden
            />
            <span>Encrypted in transit</span>
            <span aria-hidden>·</span>
            <span>Private by design</span>
            <span aria-hidden>·</span>
            <span>Yours to control</span>
          </p>
        </section>

        <section
          aria-label="How MedVault helps"
          className="landing-enter landing-enter-7 border-t border-white/10 py-12 sm:py-14"
        >
          <ul className="grid gap-8 sm:grid-cols-3 sm:gap-6">
            {FEATURES.map((feature, index) => (
              <li key={feature.n}>
                <Link
                  href="/register"
                  className="landing-feature group block rounded-lg p-1 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-[var(--landing-accent)]"
                  style={{ ["--i" as string]: index }}
                >
                  <span className="landing-feature-n mb-4 inline-flex size-9 items-center justify-center rounded-md border font-mono text-[0.7rem] tabular-nums transition-[border-color,color,box-shadow,transform] duration-200 group-hover:-translate-y-0.5">
                    {feature.n}
                  </span>
                  <h2 className="font-heading text-base font-semibold tracking-tight text-white transition-colors duration-200 group-hover:text-[var(--landing-accent-bright)]">
                    {feature.title}
                  </h2>
                  <p className="mt-2 max-w-[28ch] text-sm leading-relaxed text-white/50 text-pretty transition-colors duration-200 group-hover:text-white/65">
                    {feature.description}
                  </p>
                  <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[var(--landing-accent)] opacity-0 transition-[opacity,transform] duration-200 group-hover:translate-x-0.5 group-hover:opacity-100 group-focus-visible:opacity-100">
                    Start here
                    <ArrowRight className="size-3" aria-hidden />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="landing-enter landing-enter-8 relative z-10 mx-auto flex w-full max-w-5xl items-center justify-center gap-2 px-5 py-8 text-xs text-white/35 sm:px-8">
        <Lock className="size-3.5 shrink-0" aria-hidden />
        Your data is encrypted and never shared.
      </footer>
    </div>
  );
}
