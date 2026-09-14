import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { register, login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../utils/errorUtils";
import BrandIcon from "../components/BrandIcon";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { token, login: storeToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      await register(email, password);
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

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setValidationError("Password must be at least 8 characters.");
      return;
    }

    mutation.mutate();
  }

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
