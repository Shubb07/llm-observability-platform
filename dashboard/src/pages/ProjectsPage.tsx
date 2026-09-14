import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/projects";
import { extractErrorMessage } from "../utils/errorUtils";
import { formatRelativeDate } from "../utils/formatters";

/**
 * FILE: src/pages/ProjectsPage.tsx
 *
 * WEEK 2: real project list.
 *
 * useQuery vs useMutation (see LoginPage for useMutation):
 *   useQuery is for GET requests that just READ data. It fires automatically
 *   on mount (and again whenever the cache goes stale - see queryClient's
 *   staleTime in App.tsx), and gives us back { data, isLoading, isError, error }.
 *   We don't call anything to "trigger" it - just describe what to fetch.
 *
 * queryKey: ["projects"] - TanStack Query caches results under this key.
 *   CreateProjectPage invalidates this same key after creating a project, so
 *   coming back here automatically refetches instead of showing stale data.
 */
export default function ProjectsPage() {
  const { data: projects, isLoading, isError, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Projects</h2>
          <p>Your LLM observability projects</p>
        </div>
        <Link to="/projects/new" className="btn btn-primary">
          + New Project
        </Link>
      </div>

      <div className="page-body">
        {isLoading && (
          <div className="state-container">
            <div className="spinner" />
          </div>
        )}

        {isError && (
          <div className="state-container">
            <div className="state-icon">⚠️</div>
            <p className="state-message">Couldn't load projects</p>
            <p className="state-hint">{extractErrorMessage(error)}</p>
          </div>
        )}

        {projects && projects.length === 0 && (
          <div className="state-container">
            <div className="state-icon">📋</div>
            <p className="state-message">No projects yet</p>
            <p className="state-hint">
              Create a project to get an API key and start sending traces.
            </p>
            <Link to="/projects/new" className="btn btn-primary" style={{ marginTop: "8px" }}>
              + New Project
            </Link>
          </div>
        )}

        {projects && projects.length > 0 && (
          <div className="card-grid">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}/traces`}
                className="card"
                style={{ display: "block", textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: "8px",
                  }}
                >
                  <h3 style={{ fontSize: "15px", fontWeight: 600 }}>{project.name}</h3>
                  <span
                    className={
                      project.status === "ACTIVE" ? "badge badge-success" : "badge badge-neutral"
                    }
                  >
                    {project.status}
                  </span>
                </div>
                <p className="text-muted" style={{ fontSize: "13px" }}>
                  Your role: <span className="text-mono">{project.role}</span>
                </p>
                <p className="text-muted" style={{ fontSize: "12px", marginTop: "4px" }}>
                  Created {formatRelativeDate(project.created_at)}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
