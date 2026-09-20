import apiClient from "./client";

export type TimeRange = "24h" | "7d" | "30d";

export interface AnalyticsMetrics {
  request_volume: number;
  error_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  total_tokens: number;
  total_cost: number;
}

export interface AnalyticsOut {
  time_range: string;
  overall: AnalyticsMetrics;
  by_model: (AnalyticsMetrics & { model: string })[] | null;
}

/** GET /api/v1/projects/:id/analytics */
export async function getAnalytics(
  projectId: string,
  timeRange: TimeRange
): Promise<AnalyticsOut> {
  const { data } = await apiClient.get<AnalyticsOut>(
    `/api/v1/projects/${projectId}/analytics`,
    { params: { time_range: timeRange, group_by: "model" } }
  );
  return data;
}
