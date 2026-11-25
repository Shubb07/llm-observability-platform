import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../api/projects";
import { extractErrorMessage } from "../utils/errorUtils";
import { formatRelativeDate } from "../utils/formatters";
import { WarningIcon, EmptyFolderIcon } from "../components/Icons";

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
          <div className="card-grid">
            <div className="skeleton skeleton-card" />
            <div className="skeleton skeleton-card" />
            <div className="skeleton skeleton-card" />
          </div>
        )}

        {isError && (
          <div className="state-container">
            <div className="state-icon text-error"><WarningIcon size={40} /></div>
            <p className="state-message">Couldn't load projects</p>
            <p className="state-hint">{extractErrorMessage(error)}</p>
          </div>
        )}

        {projects && projects.length === 0 && (
          <div className="state-container">
            <div className="state-icon text-muted"><EmptyFolderIcon size={40} /></div>
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
          <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-6)", alignItems: "flex-start" }}>
            <div className="card-grid" style={{ flex: "1 1 320px" }}>
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
                    Your role: <span className="text-mono text-accent">{project.role}</span>
                  </p>
                  <p className="text-muted" style={{ fontSize: "12px", marginTop: "4px" }}>
                    Created {formatRelativeDate(project.created_at)}
                  </p>
                </Link>
              ))}
            </div>
            <QuickStartPanel />
          </div>
        )}
      </div>
    </>
  );
}

// Fills the dead space next to a short project list with something actually
// useful instead of leaving it blank - how to get traces flowing, not just
// where to click next.
function QuickStartPanel() {
  const apiBaseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  return (
    <div className="card" style={{ width: "340px", flexShrink: 0 }}>
      <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "var(--space-3)" }}>
        Get started
      </h3>
      <ol
        className="text-muted"
        style={{ fontSize: "13px", lineHeight: 1.7, paddingLeft: "18px", marginBottom: "var(--space-4)" }}
      >
        <li>Open a project and copy its API key from Settings.</li>
        <li>Install the SDK and point it at this backend.</li>
        <li>Wrap a provider call - traces show up automatically.</li>
      </ol>
      <pre className="trace-text-block" style={{ fontSize: "11px", maxHeight: "none" }}>
{`import llm_observability_sdk as obs
from llm_observability_sdk.integrations.openai import instrument_openai

obs.init(api_key="<project-api-key>", base_url="${apiBaseUrl}")
client = instrument_openai(openai.OpenAI())`}
      </pre>
      <div style={{ display: "flex", gap: "var(--space-4)", marginTop: "var(--space-4)" }}>
        <a href={`${apiBaseUrl}/docs`} target="_blank" rel="noreferrer">
          API docs
        </a>
        <a
          href="https://github.com/Shubb07/llm-observability-platform/blob/master/sdk/README.md"
          target="_blank"
          rel="noreferrer"
        >
          SDK guide
        </a>
      </div>
    </div>
  );
}
