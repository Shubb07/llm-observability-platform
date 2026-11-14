// Mirrors app/schemas/trace.py in the backend.

/**
 * A single trace record returned by both the list and detail endpoints.
 * Field names match the backend TraceOut Pydantic schema EXACTLY.
 */
export interface TraceOut {
  id: string;
  project_id: string;
  client_trace_id: string | null; // SDK-generated idempotency ID, may be null for manual traces
  model: string;                  // e.g. "gpt-4o", "claude-3-5-sonnet-20241022"
  provider: string;               // e.g. "openai", "anthropic"
  prompt: string;
  completion: string | null;      // null if the call errored before a response
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;             // milliseconds as a float
  cost: number;                   // USD as a float, e.g. 0.00032
  status: string;                 // "success" | "error"
  error_message: string | null;   // only set when status = "error"
  tags: Record<string, unknown>;  // arbitrary JSON object — e.g. { "env": "prod", "version": "2" }
  created_at: string;             // ISO datetime string
  evaluations: EvaluationOut[];   // heuristic/LLM-judge scores computed for this trace
}

/**
 * One evaluator's result for a trace (e.g. "format_compliance", "safety_keywords").
 * Mirrors app/schemas/trace.py's EvaluationOut EXACTLY.
 */
export interface EvaluationOut {
  id: string;
  evaluator_name: string;
  status: string;            // "PENDING" | "RUNNING" | "COMPLETED" | "FAILED"
  score: number | null;      // 0.0-1.0, null if the evaluator failed before scoring
  reasoning: string | null;
  error_message: string | null;
  created_at: string;
}

/**
 * Returned by GET /api/v1/projects/:id/traces
 * A paginated wrapper around a list of traces.
 */
export interface TraceListOut {
  items: TraceOut[];
  total: number;  // total matching records in the DB (across all pages)
  limit: number;  // how many were requested (default 50)
  offset: number; // how many were skipped (default 0)
}

/**
 * Parameters for the list traces endpoint.
 * All fields are optional filters.
 */
export interface TraceFilters {
  model?: string;
  status?: string;
  limit?: number;
  offset?: number;
}
