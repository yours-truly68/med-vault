"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { LoadingGrid } from "@/components/shared";
import { useAuthStore } from "@/stores/auth-store";

type AuthGuardProps = {
  children: ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (hasHydrated && !isAuthenticated) {
      router.replace("/login");
    }
  }, [hasHydrated, isAuthenticated, router]);

  if (!hasHydrated) {
    return <LoadingGrid count={3} />;
  }

  if (!isAuthenticated) {
    return <LoadingGrid count={3} />;
  }

  return children;
}
