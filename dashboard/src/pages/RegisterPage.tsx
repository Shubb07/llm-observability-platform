import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { register, login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../utils/errorUtils";
import BrandIcon from "../components/BrandIcon";

/**
 * FILE: src/pages/RegisterPage.tsx
 * PURPOSE: The registration form. Registers the user, then auto-logs-in.
 *
 * KEY CONCEPT: WHY AUTO-LOGIN AFTER REGISTER?
 * The backend's POST /register returns UserOut { id, email } — NOT a JWT.
 * To get a JWT, you need to call POST /login separately.
 * Rather than making the user log in manually right after registering,
 * we call login() immediately behind the scenes with the same credentials.
 * This is called "auto-login" and is a standard UX pattern.
 *
 * The implementation uses two mutations sequentially:
 *   1. registerMutation — calls the register API
 *   2. On success: immediately calls login() API — same credentials
 *   3. On login success: store token → navigate
 *
 * We chain them in the onSuccess handler of the register mutation.
 */

export default function RegisterPage() {
  const navigate = useNavigate();
  const { token, login: storeToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  /**
   * Client-side validation error (for the "passwords must match" check).
   * This is purely frontend — the backend doesn't have a confirm-password field.
   * We validate this before calling the mutation.
   */
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    /**
     * mutationFn chains register → login:
     *
     * We call register() first. If it succeeds, we immediately call login()
     * with the same credentials. The token from login is then stored.
     *
     * This is "sequential async operations" — each step awaits the previous one.
     * If register() throws (e.g. email already exists), we never reach login().
     * The error is caught by TanStack Query and set on mutation.error.
     */
    mutationFn: async () => {
      await register(email, password);
      // register() succeeded → now get a JWT
      const token = await login(email, password);
      return token;
    },
    onSuccess: (token) => {
      storeToken(token.access_token);
      navigate("/projects");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setValidationError(null);

    // Client-side validation: passwords must match
    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    // Backend validation: password must be at least 8 characters (Field(min_length=8))
    if (password.length < 8) {
      setValidationError("Password must be at least 8 characters.");
      return;
    }

    mutation.mutate();
  }

  // Already-authenticated guard — same pattern as LoginPage. Must come after
  // every hook call above (useState, useMutation) — an early return before a
  // hook violates React's Rules of Hooks (see LoginPage.tsx for the full
  // explanation of why this ordering matters).
  if (token) {
    return <Navigate to="/projects" replace />;
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-icon">
            <BrandIcon size={22} />
          </div>
          <h1>LLM Observability</h1>
          <p>Create your account</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <div className="form-field">
              <label className="form-label" htmlFor="register-email">
                Email
              </label>
              <input
                id="register-email"
                type="email"
                className="form-input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="register-password">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                className="form-input"
                placeholder="Min. 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="new-password"
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="register-confirm-password">
                Confirm password
              </label>
              <input
                id="register-confirm-password"
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="new-password"
              />
            </div>
          </div>

          {/* Show client-side validation error OR server-side API error */}
          {validationError && (
            <p className="form-error" role="alert">
              {validationError}
            </p>
          )}
          {mutation.isError && (
            <p className="form-error" role="alert">
              {extractErrorMessage(mutation.error)}
            </p>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={mutation.isPending}
            style={{ marginTop: "8px" }}
          >
            {mutation.isPending ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
