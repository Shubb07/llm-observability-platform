// Mirrors app/schemas/alert.py and app/models/alert.py's ALLOWED_* sets in the backend.

export const ALERT_METRICS = [
  "request_volume",
  "error_rate",
  "p50_latency_ms",
  "p95_latency_ms",
  "p99_latency_ms",
  "total_tokens",
  "total_cost",
] as const;

export const ALERT_OPERATORS = [">", ">=", "<", "<="] as const;

export const ALERT_TIME_RANGES = ["24h", "7d", "30d"] as const;

/**
 * Returned by GET/POST/PATCH /api/v1/projects/:id/alerts
 */
export interface AlertRuleOut {
  id: string;
  project_id: string;
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  time_range: string;
  webhook_url: string;
  is_active: boolean;
  // Written only by the scheduled checker (app/workers/alert_checker.py),
  // never by anything the dashboard sends - read-only from here.
  is_breached: boolean;
  last_checked_at: string | null;
  last_triggered_at: string | null;
  created_at: string;
}

/**
 * Body for POST /api/v1/projects/:id/alerts
 */
export interface AlertRuleCreate {
  name: string;
  metric: string;
  operator: string;
  threshold: number;
  time_range: string;
  webhook_url: string;
  is_active: boolean;
}

/**
 * Body for PATCH /api/v1/projects/:id/alerts/:alertId - all optional,
 * only the fields actually changed get sent.
 */
export type AlertRuleUpdate = Partial<AlertRuleCreate>;
