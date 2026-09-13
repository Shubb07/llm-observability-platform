import type { TraceFilters, TraceListOut, TraceOut } from "../types/trace";
import apiClient from "./client";

/**
 * GET /api/v1/projects/:id/traces
 * Supports optional filters: model, status, limit, offset
 *
 * NOTE: The backend uses `alias="status"` for the query param, so we send
 * `?status=success` even though the Python param is named `status_filter`.
 * We send it as "status" in the URL — that's what the backend reads.
 */
export async function listTraces(
  projectId: string,
  filters: TraceFilters = {}
): Promise<TraceListOut> {
  const { data } = await apiClient.get<TraceListOut>(
    `/api/v1/projects/${projectId}/traces`,
    { params: filters }
  );
  return data;
}

/** GET /api/v1/projects/:id/traces/:traceId — full trace detail */
export async function getTrace(projectId: string, traceId: string): Promise<TraceOut> {
  const { data } = await apiClient.get<TraceOut>(
    `/api/v1/projects/${projectId}/traces/${traceId}`
  );
  return data;
}
