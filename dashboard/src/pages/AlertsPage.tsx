import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAlertRule, deleteAlertRule, listAlertRules, updateAlertRule } from "../api/alerts";
import { ALERT_METRICS, ALERT_OPERATORS, ALERT_TIME_RANGES } from "../types/alert";
import type { AlertRuleCreate, AlertRuleOut } from "../types/alert";
import { extractErrorMessage } from "../utils/errorUtils";
import { formatRelativeDate } from "../utils/formatters";
import { BellIcon } from "../components/Icons";

const EMPTY_FORM: AlertRuleCreate = {
  name: "",
  metric: ALERT_METRICS[0],
  operator: ALERT_OPERATORS[0],
  threshold: 0,
  time_range: "24h",
  webhook_url: "",
  is_active: true,
};

export default function AlertsPage() {
  const { projectId = "" } = useParams();
  const queryClient = useQueryClient();
  const [dialogRule, setDialogRule] = useState<AlertRuleOut | "new" | null>(null);
  const [form, setForm] = useState<AlertRuleCreate>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const rules = useQuery({
    queryKey: ["alert-rules", projectId],
    queryFn: () => listAlertRules(projectId),
  });

  function openCreate() {
    setForm(EMPTY_FORM);
    setFormError(null);
    setDialogRule("new");
  }

  function openEdit(rule: AlertRuleOut) {
    setForm({
      name: rule.name,
      metric: rule.metric,
      operator: rule.operator,
      threshold: rule.threshold,
      time_range: rule.time_range,
      webhook_url: rule.webhook_url,
      is_active: rule.is_active,
    });
    setFormError(null);
    setDialogRule(rule);
  }

  const saveMutation = useMutation({
    mutationFn: () =>
      dialogRule === "new"
        ? createAlertRule(projectId, form)
        : updateAlertRule(projectId, (dialogRule as AlertRuleOut).id, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert-rules", projectId] });
      setDialogRule(null);
    },
    onError: (err) => setFormError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (alertId: string) => deleteAlertRule(projectId, alertId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alert-rules", projectId] }),
  });

  function handleDelete(rule: AlertRuleOut) {
    if (window.confirm(`Delete the alert rule "${rule.name}"? This can't be undone.`)) {
      deleteMutation.mutate(rule.id);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    saveMutation.mutate();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Alert Rules</h2>
          <p>Get a webhook notification when a metric crosses a threshold</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          + New Rule
        </button>
      </div>

      <div className="page-body">
        {rules.isLoading && <p className="text-muted">Loading alert rules…</p>}
        {rules.isError && (
          <p className="form-error">{extractErrorMessage(rules.error)}</p>
        )}

        {rules.data && rules.data.length === 0 && (
          <div className="state-container">
            <div className="state-icon text-muted"><BellIcon size={40} /></div>
            <p className="state-message">No alert rules yet</p>
            <p className="state-hint">
              Create one to get notified when a metric like error rate or latency crosses a threshold you set.
            </p>
          </div>
        )}

        {rules.data && rules.data.length > 0 && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Condition</th>
                  <th>Window</th>
                  <th>Status</th>
                  <th>Last Triggered</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rules.data.map((rule) => (
                  <tr key={rule.id}>
                    <td>{rule.name}</td>
                    <td className="text-mono">
                      {rule.metric} {rule.operator} {rule.threshold}
                    </td>
                    <td className="text-mono">{rule.time_range}</td>
                    <td>
                      <span className={`badge ${rule.is_active ? "badge-success" : "badge-neutral"}`}>
                        {rule.is_active ? "Active" : "Disabled"}
                      </span>
                      {rule.is_active && (
                        <span
                          className={`badge ${rule.is_breached ? "badge-error" : "badge-success"}`}
                          style={{ marginLeft: "6px" }}
                        >
                          {rule.is_breached ? "Breached" : "OK"}
                        </span>
                      )}
                    </td>
                    <td className="text-muted">
                      {rule.last_triggered_at ? formatRelativeDate(rule.last_triggered_at) : "—"}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end" }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => openEdit(rule)}>
                          Edit
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDelete(rule)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {dialogRule && (
        <div className="dialog-overlay" onClick={() => setDialogRule(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-title">
                {dialogRule === "new" ? "New Alert Rule" : "Edit Alert Rule"}
              </span>
              <button className="dialog-close" onClick={() => setDialogRule(null)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="dialog-body">
                <div className="form-group">
                  <div className="form-field">
                    <label className="form-label" htmlFor="alert-name">
                      Name
                    </label>
                    <input
                      id="alert-name"
                      type="text"
                      className="form-input"
                      placeholder="e.g. High error rate"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label">Condition</label>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <select
                        className="filter-select"
                        value={form.metric}
                        onChange={(e) => setForm({ ...form, metric: e.target.value })}
                        style={{ flex: 2 }}
                      >
                        {ALERT_METRICS.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))}
                      </select>
                      <select
                        className="filter-select"
                        value={form.operator}
                        onChange={(e) => setForm({ ...form, operator: e.target.value })}
                        style={{ flex: 1 }}
                      >
                        {ALERT_OPERATORS.map((op) => (
                          <option key={op} value={op}>
                            {op}
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        step="any"
                        className="form-input"
                        style={{ flex: 1 }}
                        value={form.threshold}
                        onChange={(e) => setForm({ ...form, threshold: Number(e.target.value) })}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-field">
                    <label className="form-label" htmlFor="alert-window">
                      Time window
                    </label>
                    <select
                      id="alert-window"
                      className="filter-select"
                      value={form.time_range}
                      onChange={(e) => setForm({ ...form, time_range: e.target.value })}
                    >
                      {ALERT_TIME_RANGES.map((tr) => (
                        <option key={tr} value={tr}>
                          {tr}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-field">
                    <label className="form-label" htmlFor="alert-webhook">
                      Webhook URL
                    </label>
                    <input
                      id="alert-webhook"
                      type="url"
                      className="form-input"
                      placeholder="https://example.com/hooks/alert"
                      value={form.webhook_url}
                      onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-field">
                    <label className="form-label" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                      />
                      Active
                    </label>
                  </div>
                </div>

                {formError && <p className="form-error">{formError}</p>}
              </div>
              <div className="dialog-header" style={{ borderTop: "1px solid var(--color-border)", borderBottom: "none" }}>
                <div className="dialog-actions" style={{ width: "100%" }}>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => setDialogRule(null)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={saveMutation.isPending}>
                    {saveMutation.isPending ? "Saving…" : "Save"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
