import { Fragment, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getAnalytics, type TimeRange } from "../api/analytics";
import { listTraces } from "../api/traces";
import { extractErrorMessage } from "../utils/errorUtils";
import {
  formatCost,
  formatDate,
  formatLatency,
  formatRelativeDate,
  formatTokens,
} from "../utils/formatters";

export default function TracesPage() {
  const { projectId = "" } = useParams();
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");
  const [status, setStatus] = useState("");
  const [model, setModel] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const analytics = useQuery({
    queryKey: ["analytics", projectId, timeRange],
    queryFn: () => getAnalytics(projectId, timeRange),
  });

  const traces = useQuery({
    queryKey: ["traces", projectId, status, model],
    queryFn: () =>
      listTraces(projectId, {
        status: status || undefined,
        model: model || undefined,
        limit: 50,
      }),
  });

  const overall = analytics.data?.overall;
  const modelNames = analytics.data?.by_model?.map((m) => m.model) ?? [];

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Trace Explorer</h2>
          <p>Every LLM call captured by the SDK for this project</p>
        </div>
        <Link to="/projects" className="btn btn-secondary btn-sm">
          ← Projects
        </Link>
      </div>

      <div className="page-body">
        <div className="metrics-toolbar">
          <span className="filter-label">Analytics window</span>
          <select
            className="filter-select"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRange)}
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>

        {analytics.isError && (
          <p className="form-error">{extractErrorMessage(analytics.error)}</p>
        )}

        {overall && (
          <div className="metric-grid">
            <Metric label="Requests" value={formatTokens(overall.request_volume)} />
            <Metric
              label="Error rate"
              value={`${(overall.error_rate * 100).toFixed(1)}%`}
              tone={overall.error_rate > 0.1 ? "error" : undefined}
            />
            <Metric label="p50 latency" value={formatLatency(overall.p50_latency_ms)} />
            <Metric label="p95 latency" value={formatLatency(overall.p95_latency_ms)} />
            <Metric label="p99 latency" value={formatLatency(overall.p99_latency_ms)} />
            <Metric label="Total tokens" value={formatTokens(overall.total_tokens)} />
            <Metric label="Total cost" value={formatCost(overall.total_cost)} />
          </div>
        )}

        <div className="metrics-toolbar" style={{ marginTop: "var(--space-6)" }}>
          <span className="filter-label">Status</span>
          <select
            className="filter-select"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>

          <span className="filter-label">Model</span>
          <select
            className="filter-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="">All</option>
            {modelNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>

          {traces.data && (
            <span className="filter-label" style={{ marginLeft: "auto" }}>
              {traces.data.total} trace{traces.data.total === 1 ? "" : "s"}
            </span>
          )}
        </div>

        {traces.isLoading && <p className="text-muted">Loading traces…</p>}
        {traces.isError && (
          <p className="form-error">{extractErrorMessage(traces.error)}</p>
        )}

        {traces.data && traces.data.items.length === 0 && (
          <div className="state-container">
            <div className="state-icon">🔭</div>
            <p className="state-message">No traces match these filters</p>
            <p className="state-hint">
              Send traces with the SDK or run the demo seed script to see data here.
            </p>
          </div>
        )}

        {traces.data && traces.data.items.length > 0 && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Model</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                  <th>Prompt</th>
                </tr>
              </thead>
              <tbody>
                {traces.data.items.map((t) => (
                  <Fragment key={t.id}>
                    <tr
                      className={expandedId === t.id ? "selected" : undefined}
                      onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}
                    >
                      <td title={formatDate(t.created_at)}>{formatRelativeDate(t.created_at)}</td>
                      <td>
                        <span className="text-mono">{t.model}</span>
                        <div className="text-muted" style={{ fontSize: "11px" }}>
                          {t.provider}
                        </div>
                      </td>
                      <td>
                        <span
                          className={
                            t.status === "success" ? "badge badge-success" : "badge badge-error"
                          }
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="text-mono">{formatLatency(t.latency_ms)}</td>
                      <td className="text-mono">
                        {formatTokens(t.prompt_tokens + t.completion_tokens)}
                      </td>
                      <td className="text-mono">{formatCost(t.cost)}</td>
                      <td className="trace-prompt-cell">{t.prompt}</td>
                    </tr>
                    {expandedId === t.id && (
                      <tr className="trace-detail-row">
                        <td colSpan={7}>
                          <div className="trace-detail">
                            <div>
                              <p className="filter-label">Prompt</p>
                              <p>{t.prompt}</p>
                            </div>
                            <div>
                              <p className="filter-label">
                                {t.status === "error" ? "Error" : "Completion"}
                              </p>
                              <p>{t.status === "error" ? t.error_message : t.completion}</p>
                            </div>
                            <div className="text-muted" style={{ fontSize: "12px" }}>
                              {t.prompt_tokens} prompt + {t.completion_tokens} completion tokens ·
                              tags {JSON.stringify(t.tags)}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "error" }) {
  return (
    <div className="metric-tile">
      <p className="metric-label">{label}</p>
      <p className={tone === "error" ? "metric-value metric-value-error" : "metric-value"}>
        {value}
      </p>
    </div>
  );
}
