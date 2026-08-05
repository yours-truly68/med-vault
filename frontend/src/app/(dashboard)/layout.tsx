import type { ReactNode } from "react";

import { AuthGuard } from "@/components/auth";
import { Navbar, Sidebar } from "@/components/layout";
import { LlmBusyBanner, LlmRateLimitWatcher } from "@/components/shared";
import { MedVaultCopilotLauncher } from "@/components/copilot/copilot-launcher";

type DashboardLayoutProps = {
  children: ReactNode;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <AuthGuard>
      {/* Floating glass shell — Figma: 0.5rem gutter + 0.5rem radius */}
      <div className="app-shell-bg min-h-dvh p-2">
        <div className="mx-auto flex h-[calc(100dvh-1rem)] max-w-[1600px] flex-col gap-2">
          <Navbar />
          <div className="flex min-h-0 flex-1 gap-2">
            <Sidebar />
            <main
              id="main-content"
              className="glass-panel flex min-h-0 flex-1 flex-col overflow-auto rounded-lg p-4 md:p-5 lg:p-6"
            >
              <div className="content-shell flex min-h-0 w-full flex-1 flex-col">
                <LlmRateLimitWatcher />
                <LlmBusyBanner />
                {children}
              </div>
            </main>
          </div>
        </div>
      </div>

      {/* Universal MedVault Copilot Floating / Docked Assistant */}
      <MedVaultCopilotLauncher />
    </AuthGuard>
  );
}
