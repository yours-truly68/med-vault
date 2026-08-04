"use client";

import Link from "next/link";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Eye, EyeOff, Lock, Mail } from "lucide-react";
import { useForm } from "react-hook-form";

import { MedVaultLogo } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";
import { loginSchema, type LoginFormValues } from "@/lib/validators/auth";
import { cn } from "@/lib/utils";

export function LoginForm() {
  const loginMutation = useLogin();
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = handleSubmit((values) => {
    loginMutation.mutate(values);
  });

  const errorMessage =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.message
      : loginMutation.error
        ? "Unable to sign in. Please try again."
        : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-center lg:hidden">
        <MedVaultLogo href="/" size="lg" priority className="[&_span]:text-white" />
      </div>

      <div className="auth-card rounded-lg border p-6 sm:p-8">
        <div className="mb-6 space-y-2 text-center sm:mb-7">
          <h1 className="font-heading text-[1.65rem] font-semibold tracking-[-0.03em] text-white text-balance">
            Welcome back
          </h1>
          <p className="text-sm leading-relaxed text-white/55">
            Sign in to access your medical vault
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-white/70">
              Email
            </Label>
            <div className="relative">
              <Mail
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-white/35"
                aria-hidden
              />
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                className="auth-input h-11 pl-10"
                {...register("email")}
              />
            </div>
            {errors.email ? (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-white/70">
              Password
            </Label>
            <div className="relative">
              <Lock
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-white/35"
                aria-hidden
              />
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Your password"
                className="auth-input h-11 pr-10 pl-10"
                {...register("password")}
              />
              <button
                type="button"
                className="absolute top-1/2 right-2.5 -translate-y-1/2 rounded-md p-1.5 text-white/40 transition-colors hover:text-white/80 focus-visible:ring-2 focus-visible:ring-[var(--auth-accent)] focus-visible:outline-none"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="size-4" aria-hidden />
                ) : (
                  <Eye className="size-4" aria-hidden />
                )}
              </button>
            </div>
            {errors.password ? (
              <p className="text-sm text-destructive">
                {errors.password.message}
              </p>
            ) : null}
          </div>

          {errorMessage ? (
            <p className="text-sm text-destructive" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <Button
            type="submit"
            size="lg"
            disabled={loginMutation.isPending}
            className={cn(
              "auth-cta mt-1 h-11 w-full gap-2 border-0 text-sm font-semibold text-white shadow-none",
              "hover:brightness-110 active:scale-[0.99]",
            )}
          >
            {loginMutation.isPending ? "Signing in..." : "Sign in"}
            {!loginMutation.isPending ? (
              <ArrowRight className="size-4" aria-hidden />
            ) : null}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-white/50">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="font-medium text-[var(--auth-accent)] underline-offset-4 transition-colors hover:text-[var(--auth-accent-bright)] hover:underline"
          >
            Create one
          </Link>
        </p>
      </div>

      <p className="flex items-center justify-center gap-2 text-center text-xs text-white/40">
        <Lock className="size-3.5 shrink-0" aria-hidden />
        Your data is encrypted and never shared.
      </p>
    </div>
  );
}
