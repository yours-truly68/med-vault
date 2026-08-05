"use client";

import Link from "next/link";
import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Eye, EyeOff, Lock, Mail, User } from "lucide-react";
import { useForm } from "react-hook-form";

import { MedVaultLogo } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRegister } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api/errors";
import {
  registerSchema,
  type RegisterFormValues,
} from "@/lib/validators/auth";
import { cn } from "@/lib/utils";

export function RegisterForm() {
  const registerMutation = useRegister();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = handleSubmit((values) => {
    registerMutation.mutate(values);
  });

  const errorMessage =
    registerMutation.error instanceof ApiError
      ? registerMutation.error.message
      : registerMutation.error
        ? "Unable to create account. Please try again."
        : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-center lg:hidden">
        <MedVaultLogo href="/" size="lg" priority className="[&_span]:text-white" />
      </div>

      <div className="auth-card rounded-lg border p-6 sm:p-8">
        <div className="mb-6 space-y-2 text-center sm:mb-7">
          <h1 className="font-heading text-2xl font-semibold tracking-[-0.025em] text-white text-balance">
            Create your vault
          </h1>
          <p className="text-sm leading-relaxed text-white/55">
            Organize prescriptions, labs, and bills for your family
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name" className="text-white/70">
              Full name
            </Label>
            <div className="relative">
              <User
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-white/35"
                aria-hidden
              />
              <Input
                id="full_name"
                autoComplete="name"
                placeholder="Your name"
                className="auth-input h-11 pl-10"
                {...register("full_name")}
              />
            </div>
            {errors.full_name ? (
              <p className="text-sm text-destructive">
                {errors.full_name.message}
              </p>
            ) : null}
          </div>

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
                autoComplete="new-password"
                placeholder="Create a password"
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

          <div className="space-y-2">
            <Label htmlFor="confirm_password" className="text-white/70">
              Confirm password
            </Label>
            <div className="relative">
              <Lock
                className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-white/35"
                aria-hidden
              />
              <Input
                id="confirm_password"
                type={showConfirm ? "text" : "password"}
                autoComplete="new-password"
                placeholder="Repeat password"
                className="auth-input h-11 pr-10 pl-10"
                {...register("confirm_password")}
              />
              <button
                type="button"
                className="absolute top-1/2 right-2.5 -translate-y-1/2 rounded-md p-1.5 text-white/40 transition-colors hover:text-white/80 focus-visible:ring-2 focus-visible:ring-[var(--auth-accent)] focus-visible:outline-none"
                onClick={() => setShowConfirm((value) => !value)}
                aria-label={
                  showConfirm ? "Hide confirm password" : "Show confirm password"
                }
              >
                {showConfirm ? (
                  <EyeOff className="size-4" aria-hidden />
                ) : (
                  <Eye className="size-4" aria-hidden />
                )}
              </button>
            </div>
            {errors.confirm_password ? (
              <p className="text-sm text-destructive">
                {errors.confirm_password.message}
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
            disabled={registerMutation.isPending}
            className={cn(
              "auth-cta mt-1 h-11 w-full gap-2 border-0 text-sm font-semibold text-white shadow-none",
              "hover:brightness-110 active:scale-[0.99]",
            )}
          >
            {registerMutation.isPending ? "Creating account..." : "Create account"}
            {!registerMutation.isPending ? (
              <ArrowRight className="size-4" aria-hidden />
            ) : null}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-white/50">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-[var(--auth-accent)] underline-offset-4 transition-colors hover:text-[var(--auth-accent-bright)] hover:underline"
          >
            Sign in
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
