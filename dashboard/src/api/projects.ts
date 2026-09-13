import type { ProjectOut, ProjectSummary } from "../types/project";
import apiClient from "./client";

/** GET /api/v1/projects — list all projects the current user belongs to */
export async function listProjects(): Promise<ProjectSummary[]> {
  const { data } = await apiClient.get<ProjectSummary[]>("/api/v1/projects");
  return data;
}

/** GET /api/v1/projects/:id — get one project (includes api_key) */
export async function getProject(projectId: string): Promise<ProjectOut> {
  const { data } = await apiClient.get<ProjectOut>(`/api/v1/projects/${projectId}`);
  return data;
}

/** POST /api/v1/projects — create a project, returns ProjectOut with api_key */
export async function createProject(name: string): Promise<ProjectOut> {
  const { data } = await apiClient.post<ProjectOut>("/api/v1/projects", { name });
  return data;
}
