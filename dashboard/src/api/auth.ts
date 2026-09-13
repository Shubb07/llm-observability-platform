import type { Token, UserOut } from "../types/auth";
import apiClient from "./client";

/**
 * WHY PURE FUNCTIONS (no React, no useState, no useEffect)?
 *
 * These functions are the "data access layer." They know HOW to talk to the
 * backend. They don't know anything about React components, loading states,
 * or caching — that's TanStack Query's job (in src/hooks/).
 *
 * Separation of concerns:
 *   api/auth.ts   → HOW to make the HTTP call
 *   hooks/        → WHEN to make it, caching, loading/error state
 *   components/   → WHAT to render based on that state
 *
 * The `<Token>` and `<UserOut>` generics tell Axios (and TypeScript) what shape
 * the response body will have. TypeScript then knows exactly what fields exist
 * on `data` — no guessing, no runtime surprises.
 */

/**
 * POST /api/v1/auth/register
 *
 * Sends { email, password } — creates a new user.
 * Returns UserOut { id, email } — NOT a JWT.
 * The caller must then call login() to get a token.
 */
export async function register(email: string, password: string): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>("/api/v1/auth/register", {
    email,
    password,
  });
  return data;
}

/**
 * POST /api/v1/auth/login
 *
 * Sends { email, password } — authenticates the user.
 * Returns Token { access_token, token_type }.
 * The caller stores access_token in localStorage.
 */
export async function login(email: string, password: string): Promise<Token> {
  const { data } = await apiClient.post<Token>("/api/v1/auth/login", {
    email,
    password,
  });
  return data;
}

/**
 * GET /api/v1/auth/me
 *
 * Fetches the current user's identity using the JWT already attached
 * by the Axios request interceptor.
 * Used on app startup to validate the stored token.
 * Returns UserOut { id, email }.
 */
export async function getMe(): Promise<UserOut> {
  const { data } = await apiClient.get<UserOut>("/api/v1/auth/me");
  return data;
}
