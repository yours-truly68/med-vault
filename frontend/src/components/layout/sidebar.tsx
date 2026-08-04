"use client";

import { SidebarNav } from "@/components/layout/sidebar-nav";

export function Sidebar() {
  return (
    <aside className="glass-panel hidden w-56 shrink-0 flex-col overflow-hidden rounded-lg text-sidebar-foreground md:flex lg:w-60">
      <SidebarNav className="p-2" />
    </aside>
  );
}
