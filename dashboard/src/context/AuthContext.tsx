import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe, logout as logoutRequest } from "../api/auth";
import type { UserOut } from "../types/auth";

interface AuthContextValue {
  user: UserOut | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  // Called once the login/register API call itself has already succeeded
  // (the backend's Set-Cookie already landed) - this just loads `user` and
  // flips isAuthenticated so the rest of the app can react.
  onAuthenticated: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // The access token itself lives in an HttpOnly cookie this app can't
  // read - whether a session exists at all is only known by asking the
  // backend. /me doubles as that check and as the user-info fetch.
  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  const onAuthenticated = useCallback(async () => {
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: user !== null, isLoading, onAuthenticated, logout }}
    >
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
