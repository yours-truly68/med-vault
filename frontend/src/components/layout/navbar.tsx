"use client";

import Link from "next/link";
import { Menu, Sparkles, Search } from "lucide-react";

import { MedVaultLogo } from "@/components/brand";
import { MobileNav } from "@/components/layout/mobile-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { getUserInitials } from "@/lib/user";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import { useCopilotStore } from "@/stores/copilot-store";

export function Navbar() {
  const user = useAuthStore((state) => state.user);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);
  const toggleCopilot = useCopilotStore((state) => state.toggleCopilot);
  const logoutMutation = useLogout();
  useCurrentUser();

  return (
    <header className="glass-panel flex h-14 shrink-0 items-center rounded-lg px-3 md:px-5">
      <div className="flex w-full items-center justify-between gap-4">
        {/* Left: Brand & Mobile Menu */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon-sm"
            className="rounded-xl md:hidden"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="size-4" />
          </Button>
          <MedVaultLogo href="/dashboard" size="sm" />
        </div>

        {/* Center: Prominent MedVault Copilot Search & Launcher Input Pill */}
        <div className="flex-1 max-w-xl mx-auto hidden sm:block">
          <button
            type="button"
            onClick={toggleCopilot}
            className="group flex w-full items-center justify-between rounded-full border border-border/80 bg-background/80 px-3.5 py-1.5 text-xs text-muted-foreground shadow-xs transition-all hover:border-brand-accent/40 hover:bg-accent/40 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="size-3.5 text-brand-accent animate-pulse" />
              <span className="font-medium text-foreground/80 group-hover:text-primary">
                Ask MedVault Copilot...
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="hidden text-[0.6875rem] text-muted-foreground md:inline">
                RAG Grounded
              </span>
              <kbd className="rounded-md border border-border/80 bg-muted px-1.5 py-0.5 text-[0.625rem] font-semibold text-muted-foreground">
                ⌘K
              </kbd>
            </div>
          </button>
        </div>

        {/* Right: Theme & Account Menu */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Mobile Copilot Trigger */}
          <Button
            variant="ghost"
            size="icon-sm"
            className="rounded-xl sm:hidden text-brand-accent"
            onClick={toggleCopilot}
            aria-label="Open MedVault Copilot"
          >
            <Sparkles className="size-4" />
          </Button>

          <ThemeToggle />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-9 gap-2 rounded-xl px-2">
                <Avatar className="size-7 rounded-xl">
                  <AvatarFallback className="rounded-xl text-[10px]">
                    {user ? getUserInitials(user.full_name) : "MV"}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden max-w-32 truncate text-sm sm:inline">
                  {user?.full_name ?? "Account"}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 rounded-xl">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span>{user?.full_name}</span>
                  <span className="text-xs font-normal text-muted-foreground">
                    {user?.email}
                  </span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/settings">Settings</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
              >
                {logoutMutation.isPending ? "Signing out..." : "Sign out"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <MobileNav />
    </header>
  );
}
