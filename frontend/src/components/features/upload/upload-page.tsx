"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { FileUp, X } from "lucide-react";
import { toast } from "sonner";

import { ProcessingQueue } from "@/components/features/upload/processing-queue";
import { EmptyState, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDocuments, useUploadDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";
import { ApiError } from "@/lib/api/errors";
import { formatFileSize } from "@/lib/format";

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/jpg",
  "image/png",
];

export function UploadPageContent() {
  const familyMembersQuery = useFamilyMembers();
  const documentsQuery = useDocuments({ pollWhileProcessing: true });
  const uploadMutation = useUploadDocuments();
  const [familyMemberId, setFamilyMemberId] = useState<string>("");
  const [files, setFiles] = useState<File[]>([]);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const selected = Array.from(event.target.files ?? []);
      const valid = selected.filter((file) => ACCEPTED_TYPES.includes(file.type));
      const invalidCount = selected.length - valid.length;

      if (invalidCount > 0) {
        toast.error("Some files were skipped. Only PDF, JPG, and PNG are supported.");
      }

      setFiles((current) => [...current, ...valid]);
      event.target.value = "";
    },
    [],
  );

  const removeFile = useCallback((index: number) => {
    setFiles((current) => current.filter((_, i) => i !== index));
  }, []);

  const members = familyMembersQuery.data?.items ?? [];
  const selectedFamilyMemberId = familyMemberId || members[0]?.id || "";

  const memberMap = useMemo(() => {
    return new Map(members.map((member) => [member.id, member]));
  }, [members]);

  const canUpload = useMemo(
    () =>
      Boolean(selectedFamilyMemberId && files.length > 0 && !uploadMutation.isPending),
    [selectedFamilyMemberId, files.length, uploadMutation.isPending],
  );

  const handleUpload = async () => {
    if (!selectedFamilyMemberId || files.length === 0) return;

    try {
      const result = await uploadMutation.mutateAsync({
        familyMemberId: selectedFamilyMemberId,
        files,
      });
      toast.success(
        `Uploaded ${result.total} document${result.total === 1 ? "" : "s"}. Processing has started.`,
      );
      setFiles([]);
      void documentsQuery.refetch();
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Upload failed. Please try again.";
      toast.error(message);
    }
  };

  if (familyMembersQuery.isLoading) {
    return (
      <>
        <PageHeader
          title="Upload"
          description="Add prescriptions, lab reports, bills, and imaging files."
        />
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="animate-pulse">
            <CardHeader>
              <div className="h-5 w-40 rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-40 rounded bg-muted" />
            </CardContent>
          </Card>
          <Card className="animate-pulse">
            <CardHeader>
              <div className="h-5 w-36 rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="h-16 rounded bg-muted" />
                <div className="h-16 rounded bg-muted" />
              </div>
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  if (familyMembersQuery.isError) {
    return (
      <>
        <PageHeader title="Upload" />
        <EmptyState
          icon={FileUp}
          title="Unable to load family members"
          description="Add a family member before uploading documents."
          action={
            <Button asChild>
              <Link href="/family-members">Manage family members</Link>
            </Button>
          }
        />
      </>
    );
  }

  if (members.length === 0) {
    return (
      <>
        <PageHeader
          title="Upload"
          description="Add prescriptions, lab reports, bills, and imaging files."
        />
        <EmptyState
          icon={FileUp}
          title="Add a family member first"
          description="Every document is organized by family member. Create at least one profile to start uploading."
          action={
            <Button asChild>
              <Link href="/family-members">Add family member</Link>
            </Button>
          }
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Upload"
        description="Add prescriptions, lab reports, bills, and imaging files. We'll extract text, classify, and summarize automatically."
      />

      <div className="grid items-start gap-4 lg:grid-cols-2">
        <Card className="border-border/70 bg-card/80 shadow-tinted">
          <CardHeader>
            <CardTitle>Document details</CardTitle>
            <CardDescription>
              Choose who this upload belongs to, then select one or more files.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="family-member">Family member</Label>
              <Select
                value={selectedFamilyMemberId}
                onValueChange={setFamilyMemberId}
              >
                <SelectTrigger id="family-member">
                  <SelectValue placeholder="Select family member" />
                </SelectTrigger>
                <SelectContent>
                  {members.map((member) => (
                    <SelectItem key={member.id} value={member.id}>
                      {member.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="files">Files</Label>
              <label
                htmlFor="files"
                className="dropzone flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 px-6 py-10 text-center transition-[border-color,background-color] duration-200 hover:border-primary/40 hover:bg-muted/30"
              >
                <FileUp className="mb-3 size-8 text-muted-foreground" />
                <span className="text-sm font-medium">
                  Drop files here or click to browse
                </span>
                <span className="mt-1 text-xs text-muted-foreground">
                  PDF, JPG, or PNG up to your server limit
                </span>
                <input
                  id="files"
                  type="file"
                  multiple
                  accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
                  className="sr-only"
                  onChange={handleFileChange}
                />
              </label>
            </div>

            {files.length > 0 ? (
              <ul className="space-y-2">
                {files.map((file, index) => (
                  <li
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-sm"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => removeFile(index)}
                      aria-label={`Remove ${file.name}`}
                    >
                      <X className="size-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}

            <Button
              className="w-full sm:w-auto"
              disabled={!canUpload}
              onClick={() => void handleUpload()}
            >
              {uploadMutation.isPending
                ? "Uploading..."
                : `Upload ${files.length || ""} file${files.length === 1 ? "" : "s"}`}
            </Button>
          </CardContent>
        </Card>

        <ProcessingQueue
          documents={documentsQuery.data?.items ?? []}
          memberMap={memberMap}
          isLoading={documentsQuery.isLoading}
        />
      </div>
    </>
  );
}
