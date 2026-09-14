import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createProject } from "../api/projects";
import { extractErrorMessage } from "../utils/errorUtils";
import type { ProjectOut } from "../types/project";

/**
 * FILE: src/pages/CreateProjectPage.tsx
 *
 * Two-step page in one component:
 *   1. A name field + "Create" button
 *   2. After success: show the returned api_key once, since the backend
 *      only ever returns it at creation time (GET /projects list never
 *      includes it - see types/project.ts).
 *
 * queryClient.invalidateQueries(["projects"]) after success: tells TanStack
 * Query the cached project list is stale, so navigating back to /projects
 * refetches instead of showing the list without the new project.
 */
export default function CreateProjectPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [createdProject, setCreatedProject] = useState<ProjectOut | null>(null);
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: () => createProject(name),
    onSuccess: (project) => {
      setCreatedProject(project);
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  async function handleCopy() {
    if (!createdProject) return;
    await navigator.clipboard.writeText(createdProject.api_key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  // Step 2: project created - show the API key.
  if (createdProject) {
    return (
      <>
        <div className="page-header">
          <div>
            <h2>Project created</h2>
            <p>Save this API key now - it won't be shown again</p>
          </div>
        </div>
        <div className="page-body">
          <div className="card" style={{ maxWidth: "560px" }}>
            <p style={{ marginBottom: "4px" }}>
              <strong>{createdProject.name}</strong>
            </p>
            <p className="text-muted" style={{ fontSize: "13px", marginBottom: "12px" }}>
              Use this key as the <span className="text-mono">X-API-Key</span> header when the
              SDK sends traces to this project.
            </p>
            <div className="api-key-box">
              <span className="api-key-text">{createdProject.api_key}</span>
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleCopy}>
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              style={{ marginTop: "16px" }}
              onClick={() => navigate("/projects")}
            >
              Done
            </button>
          </div>
        </div>
      </>
    );
  }

  // Step 1: name form.
  return (
    <>
      <div className="page-header">
        <div>
          <h2>New Project</h2>
          <p>Projects isolate traces under their own API key</p>
        </div>
      </div>
      <div className="page-body">
        <form onSubmit={handleSubmit} className="card" style={{ maxWidth: "480px" }}>
          <div className="form-field">
            <label className="form-label" htmlFor="project-name">
              Project name
            </label>
            <input
              id="project-name"
              type="text"
              className="form-input"
              placeholder="e.g. Production Chatbot"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={mutation.isPending}
              required
              autoFocus
            />
          </div>

          {mutation.isError && (
            <p className="form-error" role="alert">
              {extractErrorMessage(mutation.error)}
            </p>
          )}

          <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
            <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating…" : "Create Project"}
            </button>
            <Link to="/projects" className="btn btn-ghost">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
}
