"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { useUiStore } from "@/stores/ui-store";

type FamilyMemberFilterProps = {
  className?: string;
  allowAll?: boolean;
};

export function FamilyMemberFilter({
  className,
  allowAll = true,
}: FamilyMemberFilterProps) {
  const { data, isLoading, isError } = useFamilyMembers();
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId,
  );
  const setSelectedFamilyMemberId = useUiStore(
    (state) => state.setSelectedFamilyMemberId,
  );

  if (isLoading) {
    return (
      <Select disabled>
        <SelectTrigger className={className}>
          <SelectValue placeholder="Loading members..." />
        </SelectTrigger>
      </Select>
    );
  }

  if (isError || !data?.items.length) {
    return (
      <Select disabled>
        <SelectTrigger className={className}>
          <SelectValue placeholder="No family members" />
        </SelectTrigger>
      </Select>
    );
  }

  return (
    <Select
      value={selectedFamilyMemberId ?? (allowAll ? "all" : data.items[0]?.id)}
      onValueChange={(value) =>
        setSelectedFamilyMemberId(value === "all" ? null : value)
      }
    >
      <SelectTrigger className={className}>
        <SelectValue placeholder="Filter by member" />
      </SelectTrigger>
      <SelectContent>
        {allowAll ? <SelectItem value="all">All family members</SelectItem> : null}
        {data.items.map((member) => (
          <SelectItem key={member.id} value={member.id}>
            {member.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
