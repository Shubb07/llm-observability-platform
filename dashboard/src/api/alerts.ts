import type { AlertRuleCreate, AlertRuleOut, AlertRuleUpdate } from "../types/alert";
import apiClient from "./client";

/** GET /api/v1/projects/:id/alerts — any project member can list rules */
export async function listAlertRules(projectId: string): Promise<AlertRuleOut[]> {
  const { data } = await apiClient.get<AlertRuleOut[]>(`/api/v1/projects/${projectId}/alerts`);
  return data;
}

/** POST /api/v1/projects/:id/alerts — admin only */
export async function createAlertRule(
  projectId: string,
  payload: AlertRuleCreate
): Promise<AlertRuleOut> {
  const { data } = await apiClient.post<AlertRuleOut>(
    `/api/v1/projects/${projectId}/alerts`,
    payload
  );
  return data;
}

/** PATCH /api/v1/projects/:id/alerts/:alertId — admin only */
export async function updateAlertRule(
  projectId: string,
  alertId: string,
  payload: AlertRuleUpdate
): Promise<AlertRuleOut> {
  const { data } = await apiClient.patch<AlertRuleOut>(
    `/api/v1/projects/${projectId}/alerts/${alertId}`,
    payload
  );
  return data;
}

/** DELETE /api/v1/projects/:id/alerts/:alertId — admin only */
export async function deleteAlertRule(projectId: string, alertId: string): Promise<void> {
  await apiClient.delete(`/api/v1/projects/${projectId}/alerts/${alertId}`);
}
