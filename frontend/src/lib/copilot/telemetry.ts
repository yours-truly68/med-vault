"use client";

export type CopilotTelemetryEvent =
  | { type: "response_time"; latencyMs: number }
  | { type: "citation_click"; documentId: string }
  | { type: "suggested_chip_click"; prompt: string }
  | { type: "tool_action_executed"; actionType: string }
  | { type: "satisfaction_rating"; messageId: string; rating: "up" | "down" };

class CopilotTelemetryTracker {
  private events: CopilotTelemetryEvent[] = [];

  track(event: CopilotTelemetryEvent) {
    this.events.push(event);
    console.log("[Copilot Telemetry]", event);
  }

  getMetrics() {
    const latencies = this.events
      .filter((e): e is { type: "response_time"; latencyMs: number } => e.type === "response_time")
      .map((e) => e.latencyMs);

    const avgLatency = latencies.length > 0
      ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
      : 0;

    const citationClicks = this.events.filter((e) => e.type === "citation_click").length;
    const chipClicks = this.events.filter((e) => e.type === "suggested_chip_click").length;
    const toolExecutions = this.events.filter((e) => e.type === "tool_action_executed").length;

    const ratings = this.events.filter((e): e is { type: "satisfaction_rating"; messageId: string; rating: "up" | "down" } => e.type === "satisfaction_rating");
    const positiveRatings = ratings.filter((r) => r.rating === "up").length;
    const satisfactionRate = ratings.length > 0 ? Math.round((positiveRatings / ratings.length) * 100) : 100;

    return {
      avgLatency,
      totalQueries: latencies.length,
      citationClicks,
      chipClicks,
      toolExecutions,
      satisfactionRate,
    };
  }
}

export const copilotTelemetry = new CopilotTelemetryTracker();
