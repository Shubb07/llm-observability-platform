import type { Token, UserOut } from "../types/auth";
import apiClient from "./client";

export async function register(email: string, password: string): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>(
    "/api/v1/auth/register",
    { email, password },
    { skipAuthRedirect: true }
  );
  return data;
}

export async function login(email: string, password: string): Promise<Token> {
  const { data } = await apiClient.post<Token>(
    "/api/v1/auth/login",
    { email, password },
    { skipAuthRedirect: true }
  );
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/api/v1/auth/logout", undefined, { skipAuthRedirect: true });
}

export async function getMe(): Promise<UserOut> {
  // Called on every app mount (AuthContext) just to check whether a session
  // exists - a 401 here means "not logged in yet," not "your session
  // expired," so it must not trigger the global redirect. Without this, an
  // unauthenticated visit to /login itself 401s, which reloads the page,
  // which checks again, which 401s again: an infinite reload loop.
  const { data } = await apiClient.get<UserOut>("/api/v1/auth/me", { skipAuthRedirect: true });
  return data;
}
