"use client";

import { MedVaultLogo } from "@/components/brand";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
} from "@/components/ui/sheet";
import { useUiStore } from "@/stores/ui-store";

export function MobileNav() {
  const isSidebarOpen = useUiStore((state) => state.isSidebarOpen);
  const setSidebarOpen = useUiStore((state) => state.setSidebarOpen);

  return (
    <Sheet open={isSidebarOpen} onOpenChange={setSidebarOpen}>
      <SheetContent
        side="left"
        className="w-72 rounded-r-2xl border-border/50 bg-card/90 p-0 backdrop-blur-xl"
      >
        <SheetHeader className="border-b border-border px-4 py-4 text-left">
          <MedVaultLogo size="sm" showWordmark />
          <SheetDescription className="mt-2">
            Navigate your medical records
          </SheetDescription>
        </SheetHeader>
        <SidebarNav onNavigate={() => setSidebarOpen(false)} />
      </SheetContent>
    </Sheet>
  );
}
