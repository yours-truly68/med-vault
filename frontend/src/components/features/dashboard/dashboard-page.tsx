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
import { useTimelineEvents } from "@/hooks/use-timeline";
import { formatDate } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";

import { HealthTrendsPreview } from "./health-trends-preview";

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
  const timelineQuery = useTimelineEvents({ limit: 8 });
  const selectedFamilyMemberId = useUiStore(
    (state) => state.selectedFamilyMemberId,
  );

  const isLoading =
    documentsQuery.isLoading ||
    familyMembersQuery.isLoading ||
    timelineQuery.isLoading;
  const isError =
    documentsQuery.isError || familyMembersQuery.isError || timelineQuery.isError;

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
            void timelineQuery.refetch();
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

  const diagnoses = [
    ...new Set(
      documents
        .map((doc) => doc.metadata?.diagnosis)
        .filter((value): value is string => Boolean(value)),
    ),
  ].slice(0, 4);

  const medications = documents
    .flatMap((doc) => doc.metadata?.medicines ?? [])
    .map((med) => med.name)
    .filter((name, index, arr) => arr.indexOf(name) === index)
    .slice(0, 6);

  const followUps = documents
    .filter((doc) => doc.metadata?.follow_up)
    .slice(0, 3);

  const recentLabs = documents.filter(
    (doc) =>
      doc.document_type === "lab_report" &&
      doc.status === "completed",
  ).length;

  const timelineEvents = timelineQuery.data?.items ?? [];
  const trendsMemberId =
    selectedFamilyMemberId ?? familyMembers[0]?.id ?? null;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="What is happening with your family's health right now."
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

      <div className="mb-8 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent health activity</CardTitle>
            <CardDescription>Structured events from your records</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {timelineEvents.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Upload and process documents to populate your health timeline.
              </p>
            ) : (
              timelineEvents.slice(0, 5).map((event) => (
                <div
                  key={event.id}
                  className="rounded-md border border-border/70 px-3 py-2"
                >
                  <p className="text-sm font-medium">{event.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(event.event_date)}
                    {event.description ? ` · ${event.description}` : ""}
                  </p>
                </div>
              ))
            )}
            {timelineEvents.length > 0 ? (
              <Button variant="outline" size="sm" asChild>
                <Link href="/timeline">Open timeline</Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Health snapshot</CardTitle>
            <CardDescription>Extracted from processed documents</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="mb-1 font-medium">Active conditions</p>
              {diagnoses.length ? (
                <ul className="list-disc space-y-1 pl-4 text-muted-foreground">
                  {diagnoses.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">No diagnoses extracted yet.</p>
              )}
            </div>
            <div>
              <p className="mb-1 font-medium">Medications mentioned</p>
              {medications.length ? (
                <p className="text-muted-foreground">{medications.join(", ")}</p>
              ) : (
                <p className="text-muted-foreground">No medicines found yet.</p>
              )}
            </div>
            <div>
              <p className="mb-1 font-medium">Lab reports indexed</p>
              <p className="text-muted-foreground">{recentLabs}</p>
            </div>
            {followUps.length > 0 ? (
              <div>
                <p className="mb-1 font-medium">Follow-up notes</p>
                <ul className="space-y-1 text-muted-foreground">
                  {followUps.map((doc) => (
                    <li key={doc.id} className="line-clamp-2">
                      {doc.metadata?.follow_up}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <HealthTrendsPreview familyMemberId={trendsMemberId} />
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
