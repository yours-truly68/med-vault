"use client";

import { useTheme } from "next-themes";
import { useEffect, useState, type ReactNode } from "react";
import { LogOut, Monitor, Moon, Sun } from "lucide-react";

import { ErrorState, PageHeader } from "@/components/shared";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { formatDate, formatDateTime } from "@/lib/format";
import { getUserInitials } from "@/lib/user";
import { cn } from "@/lib/utils";

function SettingsSection({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("surface-panel overflow-hidden", className)}>
      <div className="border-b border-border/60 px-5 py-4">
        <h2 className="font-heading text-base font-semibold tracking-tight text-foreground">
          {title}
        </h2>
        <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="px-5 py-1">{children}</div>
    </section>
  );
}

function SettingsRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-border/60 py-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 space-y-0.5">
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      <div className="shrink-0 sm:min-w-[12rem]">{children}</div>
    </div>
  );
}

function SettingsPageSkeleton() {
  return (
    <div className="space-y-6">
      <section className="surface-panel overflow-hidden p-5">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
          <Skeleton className="size-16 rounded-2xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-3 w-36" />
          </div>
        </div>
      </section>
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-44 rounded-lg" />
        <Skeleton className="h-44 rounded-lg" />
      </div>
    </div>
  );
}

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const;

export function SettingsPageContent() {
  const { data: user, isLoading, isError, refetch } = useCurrentUser();
  const logoutMutation = useLogout();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Settings"
          description="Manage your account and preferences."
        />
        <SettingsPageSkeleton />
      </>
    );
  }

  if (isError || !user) {
    return (
      <>
        <PageHeader title="Settings" />
        <ErrorState
          message="We couldn't load your profile."
          onRetry={() => void refetch()}
        />
      </>
    );
  }

  const activeTheme = mounted ? (theme ?? "system") : "system";
  const ThemeIcon =
    THEME_OPTIONS.find((option) => option.value === activeTheme)?.icon ??
    Monitor;

  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your account and preferences."
      />

      <div className="space-y-6">
        <section className="surface-panel overflow-hidden">
          <div className="flex flex-col gap-5 p-5 sm:flex-row sm:items-center sm:gap-6">
            <Avatar className="size-16 rounded-2xl ring-2 ring-border/60">
              <AvatarFallback className="rounded-2xl bg-accent text-lg font-semibold text-primary">
                {getUserInitials(user.full_name)}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 space-y-1">
              <h2 className="font-heading text-xl font-semibold tracking-tight text-foreground text-balance">
                {user.full_name}
              </h2>
              <p className="text-sm text-muted-foreground">{user.email}</p>
              <p className="text-xs text-muted-foreground">
                Member since {formatDate(user.created_at)}
              </p>
            </div>
          </div>

          <div className="border-t border-border/60 px-5 py-1">
            <SettingsRow label="Full name" description="Your display name in MedVault">
              <p className="text-sm font-medium text-foreground sm:text-right">
                {user.full_name}
              </p>
            </SettingsRow>
            <SettingsRow label="Email" description="Used to sign in and recover access">
              <p className="break-all text-sm font-medium text-foreground sm:text-right">
                {user.email}
              </p>
            </SettingsRow>
            <SettingsRow
              label="Account created"
              description="When you joined MedVault"
            >
              <p className="text-sm font-medium text-foreground tabular-nums sm:text-right">
                {formatDateTime(user.created_at)}
              </p>
            </SettingsRow>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          <SettingsSection
            title="Appearance"
            description="Choose how MedVault looks on this device"
          >
            <SettingsRow
              label="Theme"
              description="Light, dark, or match your system preference"
            >
              <div className="flex w-full items-center gap-2 sm:justify-end">
                <ThemeIcon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                <Select value={activeTheme} onValueChange={setTheme}>
                  <SelectTrigger id="theme" className="w-full sm:w-44">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {THEME_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </SettingsRow>
          </SettingsSection>

          <SettingsSection
            title="Session"
            description="Control access on this device"
          >
            <SettingsRow
              label="Sign out"
              description="End your session and return to the login screen"
            >
              <Button
                variant="outline"
                className="w-full sm:w-auto"
                onClick={() => logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
              >
                <LogOut className="size-4" aria-hidden />
                {logoutMutation.isPending ? "Signing out..." : "Sign out"}
              </Button>
            </SettingsRow>
          </SettingsSection>
        </div>
      </div>
    </>
  );
}
