// Mirrors app/schemas/project.py in the backend.

/**
 * Returned by GET /api/v1/projects (the list endpoint).
 * Note: does NOT include api_key — that's intentional (don't expose keys in lists).
 * Includes the current user's role in this project.
 */
export interface ProjectSummary {
  id: string;
  name: string;
  status: string;     // "ACTIVE" | "ARCHIVED"
  role: string;       // "ADMIN" | "MEMBER" | "VIEWER"
  created_at: string; // ISO datetime string — e.g. "2026-09-08T10:30:00Z"
}

/**
 * Returned by:
 *   POST /api/v1/projects   (create — includes the api_key on creation)
 *   GET  /api/v1/projects/:id  (single project fetch)
 *
 * api_key is "llmobs_<random>" — only returned here, not in the list.
 */
export interface ProjectOut {
  id: string;
  name: string;
  api_key: string;
  status: string;
  created_at: string;
}

/**
 * Returned by GET /api/v1/projects/:id/members
 */
export interface MemberOut {
  user_id: string;
  email: string;
  role: string; // "ADMIN" | "MEMBER" | "VIEWER"
}
