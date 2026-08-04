import {
  FileText,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Upload,
  Users,
  Clock3,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Upload", href: "/upload", icon: Upload },
  { label: "Documents", href: "/documents", icon: FileText },
  { label: "Timeline", href: "/timeline", icon: Clock3 },
  { label: "AI Chat", href: "/chat", icon: MessageSquare },
  { label: "Family Members", href: "/family-members", icon: Users },
  { label: "Settings", href: "/settings", icon: Settings },
];
