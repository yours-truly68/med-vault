"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { FileUp, Loader2, Upload, X } from "lucide-react";
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
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = new Set([
  "application/pdf",
  "image/jpeg",
  "image/jpg",
  "image/png",
]);

function isAcceptedFile(file: File): boolean {
  if (ACCEPTED_TYPES.has(file.type)) return true;
  const lower = file.name.toLowerCase();
  return (
    lower.endsWith(".pdf") ||
    lower.endsWith(".jpg") ||
    lower.endsWith(".jpeg") ||
    lower.endsWith(".png")
  );
}

export function UploadPageContent() {
  const familyMembersQuery = useFamilyMembers();
  const documentsQuery = useDocuments({ pollWhileProcessing: true });
  const uploadMutation = useUploadDocuments();
  const [familyMemberId, setFamilyMemberId] = useState<string>("");
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const addFiles = useCallback((incoming: File[]) => {
    const valid = incoming.filter(isAcceptedFile);
    const invalidCount = incoming.length - valid.length;

    if (invalidCount > 0) {
      toast.error("Some files were skipped. Only PDF, JPG, and PNG are supported.");
    }
    if (valid.length === 0) return;

    setFiles((current) => {
      const seen = new Set(current.map((file) => `${file.name}:${file.size}`));
      const next = valid.filter((file) => !seen.has(`${file.name}:${file.size}`));
      return [...current, ...next];
    });
  }, []);

  const handleFileChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      addFiles(Array.from(event.target.files ?? []));
      event.target.value = "";
    },
    [addFiles],
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
              Choose who this upload belongs to, then drop one or more files.
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
                onDragEnter={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={(event) => {
                  event.preventDefault();
                  setIsDragging(false);
                }}
                onDrop={(event) => {
                  event.preventDefault();
                  setIsDragging(false);
                  addFiles(Array.from(event.dataTransfer.files ?? []));
                }}
                className={cn(
                  "dropzone flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/20 px-6 py-10 text-center transition-[border-color,background-color,box-shadow] duration-200",
                  isDragging
                    ? "border-primary bg-primary/8 shadow-[inset_0_0_0_1px] shadow-primary/20"
                    : "border-border hover:border-primary/40 hover:bg-muted/30",
                )}
              >
                <Upload
                  className={cn(
                    "mb-3 size-8 transition-colors",
                    isDragging ? "text-primary" : "text-muted-foreground",
                  )}
                  aria-hidden
                />
                <span className="text-sm font-medium">
                  {isDragging ? "Drop files to add them" : "Drop files here or click to browse"}
                </span>
                <span className="mt-1 text-xs text-muted-foreground">
                  PDF, JPG, or PNG · multiple files supported
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
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Ready to upload · {files.length}
                  </p>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setFiles([])}
                  >
                    Clear all
                  </Button>
                </div>
                <ul className="max-h-48 space-y-2 overflow-y-auto pr-1">
                  {files.map((file, index) => (
                    <li
                      key={`${file.name}-${file.size}-${index}`}
                      className="flex items-center justify-between gap-3 rounded-lg border border-border/80 bg-background/50 px-3 py-2 text-sm"
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
              </div>
            ) : null}

            <Button
              className="w-full gap-2 sm:w-auto"
              disabled={!canUpload}
              onClick={() => void handleUpload()}
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden />
                  Uploading...
                </>
              ) : (
                `Upload ${files.length || ""} file${files.length === 1 ? "" : "s"}`.trim()
              )}
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
