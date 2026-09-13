import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../utils/errorUtils";

/**
 * FILE: src/pages/LoginPage.tsx
 * PURPOSE: The login form. Sends credentials to the backend, stores the JWT,
 * and redirects to /projects.
 *
 * KEY CONCEPTS DEMONSTRATED HERE:
 * 1. useMutation — for POST requests that change server state
 * 2. Controlled inputs — React owns the input values via useState
 * 3. Form submission with prevent default
 * 4. Disabled button while submitting (prevents double-submit)
 * 5. Error display from the mutation
 * 6. useNavigate — React Router's programmatic navigation
 */

export default function LoginPage() {
  /**
   * useNavigate() — React Router's hook for programmatic navigation.
   * navigate("/projects") is the equivalent of clicking a <Link to="/projects">.
   * We use it after login succeeds (we can't use a <Link> because navigation
   * depends on an async result, not a click).
   */
  const navigate = useNavigate();

  /**
   * useAuth() — reads from AuthContext. We need `login` to store the token
   * after a successful API call. Note: this `login` is our context function
   * (stores the token), not the API function `login` imported from api/auth.ts.
   * We've aliased one of them below to avoid the naming conflict.
   */
  const { token, login: storeToken } = useAuth();

  /**
   * Already-authenticated guard.
   *
   * If the user already has a token (they're logged in) and somehow lands on
   * /login (e.g. typed it manually, or hit Back after logging in), we redirect
   * them to /projects immediately. No reason to show them a login form.
   *
   * This is the public-route equivalent of ProtectedRoute — ProtectedRoute
   * keeps logged-out users away from protected pages; this keeps logged-in
   * users away from auth pages.
   *
   * `replace` prevents /login from going into the browser history, so if
   * the user presses Back they don't bounce back to /login.
   */
  if (token) {
    return <Navigate to="/projects" replace />;
  }

  /**
   * CONTROLLED INPUTS — React owns the input values.
   *
   * In React, there are two ways to handle forms:
   *   1. Controlled inputs: value comes from useState, onChange updates state.
   *      React is the "source of truth" for the value.
   *   2. Uncontrolled inputs: value lives in the DOM, you read it with a ref.
   *
   * We use controlled inputs because:
   *   - Easy to validate before submit
   *   - Easy to clear after submit
   *   - TypeScript knows the types
   *   - This is the standard React pattern
   */
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  /**
   * useMutation — for operations that CHANGE data on the server (POST, PUT, DELETE).
   *
   * Contrast with useQuery (for reading data):
   *   useQuery  → fires automatically when component mounts
   *   useMutation → fires manually when you call mutation.mutate()
   *
   * mutationFn: the async function to call.
   *   We wrap the login() API call to pass the current email/password values.
   *
   * onSuccess: called after mutationFn resolves.
   *   We receive the Token object, store the JWT via context, then navigate.
   *
   * What useMutation gives us:
   *   mutation.isPending  — true while the API call is in flight
   *   mutation.isError    — true if the last call failed
   *   mutation.error      — the AxiosError from the failed call
   *   mutation.mutate()   — call this to fire the mutation
   */
  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (token) => {
      storeToken(token.access_token);
      navigate("/projects");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    /**
     * e.preventDefault() — stop the browser's default form submit behavior.
     *
     * By default, submitting a form causes a full page reload (HTTP POST to the
     * current URL). In a React SPA we never want that — we handle submission
     * ourselves via the mutation. preventDefault() cancels the browser behavior.
     */
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Brand header */}
        <div className="auth-brand">
          <div className="auth-brand-icon">📡</div>
          <h1>LLM Observability</h1>
          <p>Sign in to your dashboard</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            {/* Email field */}
            <div className="form-field">
              <label className="form-label" htmlFor="login-email">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={email}
                /**
                 * onChange — fires every time the user types.
                 * e.target.value is the current string in the input.
                 * We call setEmail to update state → React re-renders → input shows new value.
                 * This is the controlled input loop.
                 */
                onChange={(e) => setEmail(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            {/* Password field */}
            <div className="form-field">
              <label className="form-label" htmlFor="login-password">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          {/**
           * Error display — only rendered when the mutation has failed.
           *
           * mutation.isError is true after a failed mutate() call.
           * mutation.error holds the AxiosError thrown by the login() function.
           * extractErrorMessage() converts it to a readable string.
           *
           * The backend returns: { "detail": "Incorrect email or password" }
           * Our utility extracts "Incorrect email or password" from that.
           */}
          {mutation.isError && (
            <p className="form-error" role="alert">
              {extractErrorMessage(mutation.error)}
            </p>
          )}

          {/**
           * Submit button — disabled while mutation.isPending.
           *
           * isPending is true from the moment mutate() is called until the
           * API response arrives. Disabling the button during this window
           * prevents duplicate submissions (user clicking twice).
           *
           * The label change ("Signing in...") communicates progress to the user
           * without needing a separate loading spinner.
           */}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={mutation.isPending}
            style={{ marginTop: "8px" }}
          >
            {mutation.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="auth-footer">
          Don't have an account?{" "}
          <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  );
}
