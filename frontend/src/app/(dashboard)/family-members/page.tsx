import type { Metadata } from "next";

import { FamilyMembersPageContent } from "@/components/features/family-members/family-members-page";

export const metadata: Metadata = {
  title: "Family Members",
};

export default function FamilyMembersPage() {
  return <FamilyMembersPageContent />;
}
