import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe } from "../api/auth";
import type { UserOut } from "../types/auth";

// ---------------------------------------------------------------------------
// Cookie helpers
// WHY COOKIES instead of localStorage?
// Cookies survive cross-tab navigation, can be flagged Secure/SameSite by the
// browser/server, and work with SSR if we ever add it. We keep them
// accessible from JS (HttpOnly=false) because the Axios interceptor needs to
// read the value client-side. Set a short Max-Age matching the backend's
// JWT_EXPIRE_MINUTES (24 h = 86400 s).
// ---------------------------------------------------------------------------
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

/**
 * WHAT IS REACT CONTEXT?
 *
 * React components normally share data by passing props. But some data is needed
 * in many components at different levels of the tree — "token" is needed in the
 * Axios interceptor logic, the sidebar (to show the user's email), the logout button,
 * and ProtectedRoute. Passing token as a prop through every parent → child would be
 * painful ("prop drilling").
 *
 * Context solves this. You:
 *   1. Create a context with createContext()
 *   2. Wrap your app in <AuthContext.Provider value={...}>
 *   3. Any descendent component can read the value with useContext(AuthContext)
 *
 * The value in the Provider is shared to ALL children automatically.
 */

/** The shape of everything AuthContext provides. */
interface AuthContextValue {
  /** The raw JWT string, or null if not logged in. */
  token: string | null;
  /** The current user's id and email, or null if not authenticated. */
  user: UserOut | null;
  /**
   * Call this after a successful login API call.
   * Stores the token in a cookie and triggers a /me fetch to populate user.
   */
  login: (token: string) => void;
  /** Clears token + user from state and cookie. */
  logout: () => void;
  /**
   * True while the app is verifying the stored token on startup.
   * Use this to show a loading spinner instead of briefly flashing the login page.
   */
  isLoading: boolean;
}

/**
 * createContext() creates the context object.
 *
 * WHY `null as unknown as AuthContextValue`?
 * The default value is what you get if you call useContext() OUTSIDE of a Provider.
 * That's a programming error — it means you forgot to wrap your app. Setting it to
 * null (cast to the right type) means TypeScript won't force a pointless default,
 * and we catch the "used outside Provider" mistake at runtime with a guard below.
 */
const AuthContext = createContext<AuthContextValue>(null as unknown as AuthContextValue);

/**
 * The Provider component wraps the entire app (in main.tsx).
 * It holds the actual state and exposes it to all children via context.
 *
 * Props: { children } — React's way of saying "render whatever is nested inside me."
 * In JSX: <AuthProvider><App /></AuthProvider>
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  /**
   * useState — React's hook for component-level state.
   *
   * `useState<string | null>(getCookie(TOKEN_COOKIE))`
   * The initial value is whatever is in the cookie right now.
   * This means if you close and reopen the browser, you're still logged in
   * (until the cookie expires after 24 h).
   *
   * When token changes (via setToken), React re-renders this component and
   * all consumers of the context get the new value.
   */
  const [token, setToken] = useState<string | null>(getCookie(TOKEN_COOKIE));
  const [user, setUser] = useState<UserOut | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(!!getCookie(TOKEN_COOKIE));
  // isLoading starts true only if there's a token to validate (no token = no loading needed)

  /**
   * useEffect — React's hook for side effects.
   *
   * WHAT IS A SIDE EFFECT?
   * Anything that reaches outside of rendering — fetching data, updating localStorage,
   * setting timers. React renders components "purely" (no side effects), then runs
   * useEffect after the render is committed to the screen.
   *
   * This effect runs when `token` changes (and on first mount).
   * - If there's a token: validate it by calling GET /auth/me
   * - If /me succeeds: the token is valid → set user
   * - If /me fails (401): token is expired → the Axios interceptor already
   *   redirected to /login, but we also clear local state just in case
   * - If there's no token: nothing to do, user isn't logged in
   */
  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    getMe()
      .then((me) => setUser(me))
      .catch(() => {
        // Token is invalid or expired. Axios interceptor handles the redirect.
        // We clear local state as a defensive measure.
        setToken(null);
        setUser(null);
        deleteCookie(TOKEN_COOKIE);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  /**
   * useCallback — memoizes the function so it doesn't get recreated on every render.
   *
   * WHY? Functions defined inside components are recreated on every re-render.
   * If you pass a function as a prop or context value, child components see a "new"
   * function each time and may re-render unnecessarily. useCallback caches the function
   * and only recreates it if the dependencies (the [] array) change.
   *
   * For login/logout, the dependencies are empty [] — they never change.
   */
  const login = useCallback((newToken: string) => {
    setCookie(TOKEN_COOKIE, newToken, COOKIE_MAX_AGE);
    setToken(newToken);
    // The useEffect above will trigger because `token` changed,
    // and it will call getMe() to populate `user`.
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

/**
 * Custom hook — useAuth()
 *
 * WHY A CUSTOM HOOK instead of calling useContext(AuthContext) directly?
 * Two reasons:
 *   1. Convenience: `const { token, user } = useAuth()` reads better than
 *      `const { token, user } = useContext(AuthContext)`
 *   2. Safety: we can add a runtime guard here — if someone calls useAuth()
 *      outside of an AuthProvider, they get a clear error instead of
 *      undefined behavior.
 *
 * This is the idiomatic pattern for context in production React codebases.
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth() must be used inside <AuthProvider>. Check main.tsx.");
  }
  return ctx;
}
