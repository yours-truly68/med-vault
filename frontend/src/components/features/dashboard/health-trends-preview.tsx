"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useHealthTrends } from "@/hooks/use-health-trends";
import { formatDate } from "@/lib/format";
import type { HealthTrendSeries } from "@/types/api";

function TrendSparkline({ series }: { series: HealthTrendSeries }) {
  const points = series.points;
  if (points.length === 0) return null;

  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const latest = points[points.length - 1];

  return (
    <div className="rounded-md border border-border/70 px-3 py-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{series.test_name}</p>
          <p className="text-xs text-muted-foreground">
            Latest: {latest.value}
            {latest.unit ? ` ${latest.unit}` : ""} · {formatDate(latest.date)}
          </p>
        </div>
        <div
          className="flex h-8 items-end gap-0.5"
          aria-hidden
          title={`${points.length} measurements`}
        >
          {points.slice(-8).map((point, index) => {
            const height = ((point.value - min) / range) * 100;
            return (
              <span
                key={`${point.document_id}-${index}`}
                className="w-1.5 rounded-sm bg-primary/70"
                style={{ height: `${Math.max(12, height)}%` }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

type HealthTrendsPreviewProps = {
  familyMemberId: string | null;
};

export function HealthTrendsPreview({ familyMemberId }: HealthTrendsPreviewProps) {
  const trendsQuery = useHealthTrends(familyMemberId);

  if (!familyMemberId) {
    return null;
  }

  if (trendsQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Laboratory trends</CardTitle>
          <CardDescription>Loading measurements...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const series = trendsQuery.data?.series ?? [];
  if (series.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Laboratory trends</CardTitle>
        <CardDescription>
          {trendsQuery.data?.total_measurements ?? 0} measurements across{" "}
          {series.length} tests
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {series.slice(0, 4).map((item) => (
          <TrendSparkline key={item.test_name} series={item} />
        ))}
        {series.length > 4 ? (
          <Button variant="outline" size="sm" asChild>
            <Link href="/timeline">View full health history</Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}
