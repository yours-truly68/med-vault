import type { ReactNode } from "react";

import { AuthBrandPanel } from "@/components/auth/auth-brand-panel";

type AuthLayoutProps = {
  children: ReactNode;
};

/**
 * Auth surface: dark Persuade split inspired by brand kit mock.
 * Always dark so the vault branding reads the same regardless of app theme.
 */
export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="auth-shell dark relative grid min-h-dvh lg:grid-cols-2">
      <AuthBrandPanel />
      <div className="auth-form-pane relative flex items-center justify-center p-5 sm:p-8">
        <div className="auth-form-ambient" aria-hidden />
        <div className="relative z-10 w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  );
}
