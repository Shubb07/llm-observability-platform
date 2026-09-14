import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../utils/errorUtils";
import BrandIcon from "../components/BrandIcon";

export default function LoginPage() {
  const navigate = useNavigate();
  const { token, login: storeToken } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (token) => {
      storeToken(token.access_token);
      navigate("/projects");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
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
          <p>Sign in to your dashboard</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
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
                onChange={(e) => setEmail(e.target.value)}
                disabled={mutation.isPending}
                required
                autoComplete="email"
                autoFocus
              />
            </div>

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
