"use client";

import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  Upload,
  Users,
} from "lucide-react";

import { DocumentCard } from "@/components/documents";
import { EmptyState, ErrorState, LoadingGrid, PageHeader } from "@/components/shared";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDocuments } from "@/hooks/use-documents";
import { useFamilyMembers } from "@/hooks/use-family-members";

function StatCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: number;
  description: string;
  icon: typeof FileText;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="size-4 text-muted-foreground" aria-hidden />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export function DashboardPageContent() {
  const documentsQuery = useDocuments();
  const familyMembersQuery = useFamilyMembers();

  const isLoading = documentsQuery.isLoading || familyMembersQuery.isLoading;
  const isError = documentsQuery.isError || familyMembersQuery.isError;

  if (isLoading) {
    return (
      <>
        <PageHeader
          title="Dashboard"
          description="Your family's medical records at a glance."
        />
        <LoadingGrid count={4} />
      </>
    );
  }

  if (isError) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <ErrorState
          message="We couldn't load your dashboard data."
          onRetry={() => {
            void documentsQuery.refetch();
            void familyMembersQuery.refetch();
          }}
        />
      </>
    );
  }

  const documents = documentsQuery.data?.items ?? [];
  const familyMembers = familyMembersQuery.data?.items ?? [];
  const memberMap = new Map(familyMembers.map((member) => [member.id, member]));

  const completed = documents.filter((doc) => doc.status === "completed").length;
  const processing = documents.filter(
    (doc) => doc.status === "pending" || doc.status === "processing",
  ).length;
  const failed = documents.filter((doc) => doc.status === "failed").length;
  const recentDocuments = [...documents]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, 3);

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Your family's medical records at a glance."
        actions={
          <Button asChild>
            <Link href="/upload">
              <Upload className="size-4" />
              Upload documents
            </Link>
          </Button>
        }
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Documents"
          value={documents.length}
          description="Total uploaded records"
          icon={FileText}
        />
        <StatCard
          title="Family members"
          value={familyMembers.length}
          description="Profiles you manage"
          icon={Users}
        />
        <StatCard
          title="Ready"
          value={completed}
          description="Processed and searchable"
          icon={CheckCircle2}
        />
        <StatCard
          title="In progress"
          value={processing + failed}
          description={
            failed > 0
              ? `${processing} processing, ${failed} need attention`
              : "Awaiting OCR and AI extraction"
          }
          icon={processing > 0 ? Loader2 : AlertCircle}
        />
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Recent documents</h2>
            <p className="text-sm text-muted-foreground">
              Latest uploads across your family vault.
            </p>
          </div>
          {documents.length > 0 ? (
            <Button variant="outline" size="sm" asChild>
              <Link href="/documents">View all</Link>
            </Button>
          ) : null}
        </div>

        {documents.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No documents yet"
            description="Upload prescriptions, lab reports, or bills to start building your family's health timeline."
            action={
              <Button asChild>
                <Link href="/upload">Upload your first document</Link>
              </Button>
            }
          />
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {recentDocuments.map((document) => (
              <DocumentCard
                key={document.id}
                document={document}
                familyMember={memberMap.get(document.family_member_id)}
                href={`/documents/${document.id}`}
              />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
