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
  const { data } = await apiClient.get<UserOut>("/api/v1/auth/me");
  return data;
}
