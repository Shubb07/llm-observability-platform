import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getProject } from "../api/projects";
import { extractErrorMessage } from "../utils/errorUtils";
import { formatDate } from "../utils/formatters";

export default function ProjectSettingsPage() {
  const { projectId = "" } = useParams();
  const [copied, setCopied] = useState(false);

  const { data: project, isLoading, isError, error } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => getProject(projectId),
  });

  const handleCopy = () => {
    if (project?.api_key) {
      navigator.clipboard.writeText(project.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Project Settings</h2>
          <p>Manage your project and API keys</p>
        </div>
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
            <p className="state-message">Couldn't load project</p>
            <p className="state-hint">{extractErrorMessage(error)}</p>
          </div>
        )}

        {project && (
          <div className="settings-section">
            <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>API Key</h3>
            <p className="text-muted" style={{ marginBottom: "16px" }}>
              Use this key to authenticate your SDK. <strong>Keep it secret!</strong>
            </p>
            
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "8px", 
              padding: "12px",
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: "6px"
            }}>
              <code style={{ flex: 1, fontFamily: "monospace", fontSize: "14px" }}>
                {project.api_key}
              </code>
              <button 
                className="btn btn-secondary btn-sm" 
                onClick={handleCopy}
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>

            <div style={{ marginTop: "32px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "16px" }}>Project Details</h3>
              <div style={{ display: "grid", gap: "12px" }}>
                <div>
                  <span className="text-muted" style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Project ID</span>
                  <span className="text-mono" style={{ fontSize: "14px" }}>{project.id}</span>
                </div>
                <div>
                  <span className="text-muted" style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Created</span>
                  <span style={{ fontSize: "14px" }}>{formatDate(project.created_at)}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
