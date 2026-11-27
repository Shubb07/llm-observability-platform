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
import ModelCharts from "../components/ModelCharts";
import { RadarIcon } from "../components/Icons";

const PAGE_SIZE = 50;

export default function TracesPage() {
  const { projectId = "" } = useParams();
  const [timeRange, setTimeRange] = useState<TimeRange>("30d");
  const [status, setStatus] = useState("");
  const [model, setModel] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const analytics = useQuery({
    queryKey: ["analytics", projectId, timeRange],
    queryFn: () => getAnalytics(projectId, timeRange),
  });

  const traces = useQuery({
    queryKey: ["traces", projectId, status, model, page],
    queryFn: () =>
      listTraces(projectId, {
        status: status || undefined,
        model: model || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  });

  // Changing a filter should always land back on page 1 — otherwise a narrower
  // result set can leave `page` pointing past the new last page (empty table,
  // no obvious way back). Resetting here keeps offset and filters in sync.
  function updateStatus(value: string) {
    setStatus(value);
    setPage(0);
  }
  function updateModel(value: string) {
    setModel(value);
    setPage(0);
  }
  // The model dropdown's options come from the analytics window, so widening
  // or narrowing the time range can drop the currently-selected model from
  // the list while it's still silently applied as a traces filter. Clear it
  // whenever the time range changes so the two stay in sync.
  function updateTimeRange(value: TimeRange) {
    setTimeRange(value);
    setModel("");
    setPage(0);
  }

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
            onChange={(e) => updateTimeRange(e.target.value as TimeRange)}
          >
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>

        {analytics.isError && (
          <p className="form-error">{extractErrorMessage(analytics.error)}</p>
        )}

        {analytics.isLoading && (
          <div className="metric-grid">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="skeleton skeleton-tile" />
            ))}
          </div>
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

        {analytics.data?.by_model && (
          <ModelCharts data={analytics.data.by_model} />
        )}

        <div className="metrics-toolbar" style={{ marginTop: "var(--space-6)" }}>
          <span className="filter-label">Status</span>
          <select
            className="filter-select"
            value={status}
            onChange={(e) => updateStatus(e.target.value)}
          >
            <option value="">All</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
          </select>

          <span className="filter-label">Model</span>
          <select
            className="filter-select"
            value={model}
            onChange={(e) => updateModel(e.target.value)}
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

        {traces.isLoading && (
          <div className="table-container" style={{ padding: "var(--space-4)" }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="skeleton skeleton-row"
                style={{ marginBottom: i === 5 ? 0 : "var(--space-4)" }}
              />
            ))}
          </div>
        )}
        {traces.isError && (
          <p className="form-error">{extractErrorMessage(traces.error)}</p>
        )}

        {traces.data && traces.data.items.length === 0 && (
          <div className="state-container">
            <div className="state-icon text-muted"><RadarIcon size={40} /></div>
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
                  <th>Evaluations</th>
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
                      <td>
                        <EvaluationBadges evaluations={t.evaluations} />
                      </td>
                      <td className="trace-prompt-cell">{t.prompt}</td>
                    </tr>
                    {expandedId === t.id && (
                      <tr className="trace-detail-row">
                        <td colSpan={8}>
                          <div className="trace-detail">
                            <div className="trace-detail-grid">
                              <div>
                                <p className="trace-field-label">Prompt</p>
                                <div className="trace-text-block">{t.prompt}</div>
                              </div>
                              <div>
                                <p className="trace-field-label">
                                  {t.status === "error" ? "Error" : "Completion"}
                                </p>
                                <div
                                  className={
                                    t.status === "error"
                                      ? "trace-text-block trace-text-block-error"
                                      : "trace-text-block"
                                  }
                                >
                                  {t.status === "error" ? t.error_message : t.completion}
                                </div>
                              </div>
                            </div>

                            {t.evaluations.length > 0 && (
                              <div>
                                <p className="trace-field-label">Evaluations</p>
                                <div className="trace-eval-list">
                                  {t.evaluations.map((ev) => (
                                    <div key={ev.id} className="trace-eval-item">
                                      <span className="text-mono">{ev.evaluator_name}</span>
                                      <span className="text-muted">
                                        {ev.status === "COMPLETED"
                                          ? `score ${ev.score?.toFixed(2)} — ${ev.reasoning}`
                                          : ev.status === "FAILED"
                                            ? `failed — ${ev.error_message}`
                                            : ev.status.toLowerCase()}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            <div className="trace-detail-footer text-muted">
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

        {traces.data && traces.data.total > PAGE_SIZE && (
          <div className="metrics-toolbar" style={{ marginTop: "var(--space-4)" }}>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              ← Prev
            </button>
            <span className="filter-label">
              {page * PAGE_SIZE + 1}
              {"–"}
              {Math.min((page + 1) * PAGE_SIZE, traces.data.total)} of {traces.data.total}
            </span>
            <button
              className="btn btn-secondary btn-sm"
              disabled={(page + 1) * PAGE_SIZE >= traces.data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </>
  );
}

function EvaluationBadges({ evaluations }: { evaluations: import("../types/trace").EvaluationOut[] }) {
  if (evaluations.length === 0) {
    return <span className="text-muted" style={{ fontSize: "12px" }}>—</span>;
  }
  return (
    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
      {evaluations.map((ev) => {
        // COMPLETED scores below 1.0 flag something worth looking at (e.g. an
        // empty completion or a flagged-keyword hit) - color that the same
        // as a failed evaluator run, not the same as a clean pass.
        const tone =
          ev.status === "FAILED" || (ev.status === "COMPLETED" && (ev.score ?? 1) < 1)
            ? "badge-error"
            : ev.status === "COMPLETED"
              ? "badge-success"
              : "badge-neutral";
        return (
          <span
            key={ev.id}
            className={`badge ${tone}`}
            title={ev.status === "COMPLETED" ? ev.reasoning ?? "" : ev.error_message ?? ev.status}
            style={{ fontSize: "11px" }}
          >
            {ev.evaluator_name}
          </span>
        );
      })}
    </div>
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
