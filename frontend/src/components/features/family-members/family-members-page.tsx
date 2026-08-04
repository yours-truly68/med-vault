"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Pencil, Plus, Trash2, Users } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { EmptyState, ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useCreateFamilyMember,
  useDeleteFamilyMember,
  useFamilyMembers,
  useUpdateFamilyMember,
} from "@/hooks/use-family-members";
import { ApiError } from "@/lib/api/errors";
import { formatDate, formatRelationship } from "@/lib/format";
import type { FamilyMember, RelationshipType } from "@/types/api";

const familyMemberSchema = z.object({
  name: z.string().min(1, "Name is required"),
  relationship_type: z.enum([
    "self",
    "mother",
    "father",
    "child",
    "spouse",
    "other",
  ]),
  date_of_birth: z.string().optional(),
});

type FamilyMemberFormValues = z.infer<typeof familyMemberSchema>;

const RELATIONSHIP_OPTIONS: RelationshipType[] = [
  "self",
  "mother",
  "father",
  "child",
  "spouse",
  "other",
];

function FamilyMemberForm({
  defaultValues,
  onSubmit,
  isSubmitting,
  submitLabel,
}: {
  defaultValues?: Partial<FamilyMemberFormValues>;
  onSubmit: (values: FamilyMemberFormValues) => Promise<void>;
  isSubmitting: boolean;
  submitLabel: string;
}) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FamilyMemberFormValues>({
    resolver: zodResolver(familyMemberSchema),
    defaultValues: {
      name: defaultValues?.name ?? "",
      relationship_type: defaultValues?.relationship_type ?? "self",
      date_of_birth: defaultValues?.date_of_birth ?? "",
    },
  });

  const relationshipType = watch("relationship_type");

  return (
    <form
      onSubmit={handleSubmit((values) => onSubmit(values))}
      className="space-y-4"
    >
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input id="name" {...register("name")} />
        {errors.name ? (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        ) : null}
      </div>

      <div className="space-y-2">
        <Label>Relationship</Label>
        <Select
          value={relationshipType}
          onValueChange={(value) =>
            setValue("relationship_type", value as RelationshipType)
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {RELATIONSHIP_OPTIONS.map((option) => (
              <SelectItem key={option} value={option}>
                {formatRelationship(option)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="date_of_birth">Date of birth (optional)</Label>
        <Input id="date_of_birth" type="date" {...register("date_of_birth")} />
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : submitLabel}
      </Button>
    </form>
  );
}

export function FamilyMembersPageContent() {
  const familyMembersQuery = useFamilyMembers();
  const createMutation = useCreateFamilyMember();
  const updateMutation = useUpdateFamilyMember();
  const deleteMutation = useDeleteFamilyMember();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<FamilyMember | null>(null);

  const handleCreate = async (values: FamilyMemberFormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name,
        relationship_type: values.relationship_type,
        date_of_birth: values.date_of_birth || null,
      });
      toast.success("Family member added");
      setIsCreateOpen(false);
    } catch (error) {
      toast.error(
        error instanceof ApiError ? error.message : "Unable to add family member",
      );
    }
  };

  const handleUpdate = async (values: FamilyMemberFormValues) => {
    if (!editingMember) return;
    try {
      await updateMutation.mutateAsync({
        id: editingMember.id,
        payload: {
          name: values.name,
          relationship_type: values.relationship_type,
          date_of_birth: values.date_of_birth || null,
        },
      });
      toast.success("Family member updated");
      setEditingMember(null);
    } catch (error) {
      toast.error(
        error instanceof ApiError
          ? error.message
          : "Unable to update family member",
      );
    }
  };

  const handleDelete = async (member: FamilyMember) => {
    if (!window.confirm(`Delete ${member.name}? This cannot be undone.`)) return;
    try {
      await deleteMutation.mutateAsync(member.id);
      toast.success("Family member deleted");
    } catch (error) {
      toast.error(
        error instanceof ApiError
          ? error.message
          : "Unable to delete family member",
      );
    }
  };

  if (familyMembersQuery.isLoading) {
    return (
      <>
        <PageHeader
          title="Family Members"
          description="Manage profiles for everyone whose records you organize."
        />
        <LoadingGrid count={3} />
      </>
    );
  }

  if (familyMembersQuery.isError) {
    return (
      <>
        <PageHeader title="Family Members" />
        <ErrorState
          message="We couldn't load family members."
          onRetry={() => void familyMembersQuery.refetch()}
        />
      </>
    );
  }

  const members = familyMembersQuery.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Family Members"
        description="Manage profiles for everyone whose records you organize."
        actions={
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="size-4" />
            Add member
          </Button>
        }
      />

      {members.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No family members yet"
          description="Create a profile for yourself or a loved one before uploading documents."
          action={
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus className="size-4" />
              Add your first member
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {members.map((member) => (
            <Card key={member.id}>
              <CardHeader>
                <CardTitle>{member.name}</CardTitle>
                <CardDescription>
                  {formatRelationship(member.relationship_type)}
                  {member.date_of_birth
                    ? ` · Born ${formatDate(member.date_of_birth)}`
                    : ""}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditingMember(member)}
                >
                  <Pencil className="size-4" />
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => void handleDelete(member)}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="size-4" />
                  Delete
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add family member</DialogTitle>
            <DialogDescription>
              Create a profile to organize documents for this person.
            </DialogDescription>
          </DialogHeader>
          <FamilyMemberForm
            onSubmit={handleCreate}
            isSubmitting={createMutation.isPending}
            submitLabel="Add member"
          />
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(editingMember)}
        onOpenChange={(open) => !open && setEditingMember(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit family member</DialogTitle>
            <DialogDescription>Update profile details.</DialogDescription>
          </DialogHeader>
          {editingMember ? (
            <FamilyMemberForm
              defaultValues={{
                name: editingMember.name,
                relationship_type: editingMember.relationship_type,
                date_of_birth: editingMember.date_of_birth ?? "",
              }}
              onSubmit={handleUpdate}
              isSubmitting={updateMutation.isPending}
              submitLabel="Save changes"
            />
          ) : null}
          <DialogFooter />
        </DialogContent>
      </Dialog>
    </>
  );
}
