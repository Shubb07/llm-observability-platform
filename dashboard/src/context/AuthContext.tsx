import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe } from "../api/auth";
import type { UserOut } from "../types/auth";

const TOKEN_COOKIE = "token";
const COOKIE_MAX_AGE = 60 * 60 * 24; // 24 hours in seconds

function getCookie(name: string): string | null {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function setCookie(name: string, value: string, maxAge: number): void {
  document.cookie = `${name}=${encodeURIComponent(value)}; Max-Age=${maxAge}; Path=/; SameSite=Strict`;
}

function deleteCookie(name: string): void {
  document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Strict`;
}

interface AuthContextValue {
  token: string | null;
  user: UserOut | null;
  login: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextValue>(null as unknown as AuthContextValue);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(getCookie(TOKEN_COOKIE));
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(!!getCookie(TOKEN_COOKIE));

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    getMe()
      .then((me) => setUser(me))
      .catch(() => {
        setToken(null);
        setUser(null);
        deleteCookie(TOKEN_COOKIE);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const login = useCallback((newToken: string) => {
    setCookie(TOKEN_COOKIE, newToken, COOKIE_MAX_AGE);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    deleteCookie(TOKEN_COOKIE);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth() must be used inside <AuthProvider>. Check main.tsx.");
  }
  return ctx;
}
