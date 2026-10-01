import { Outlet, NavLink, useMatch } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import BrandIcon from "../BrandIcon";
import SidebarStatus from "./SidebarStatus";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const match = useMatch("/projects/:projectId/*");
  const isNewProject = match?.params.projectId === "new";
  const projectId = !isNewProject ? match?.params.projectId : null;

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <BrandIcon size={16} />
          </div>
          <span className="sidebar-brand-name">LLM Observability</span>
        </div>

        <nav className="sidebar-section">
          <p className="sidebar-section-label">Navigation</p>
          <div className="sidebar-nav">
            <NavLink to="/projects" end className="sidebar-nav-link">
              📋 All Projects
            </NavLink>
          </div>
        </nav>

        {projectId && (
          <nav className="sidebar-section">
            <p className="sidebar-section-label">Current Project</p>
            <div className="sidebar-nav">
              <NavLink to={`/projects/${projectId}/traces`} className="sidebar-nav-link">
                🔭 Traces
              </NavLink>
              <NavLink to={`/projects/${projectId}/settings`} className="sidebar-nav-link">
                ⚙️ Settings
              </NavLink>
            </div>
          </nav>
        )}

        <SidebarStatus />
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="sidebar-user-email">
              {user?.email ?? "Loading…"}
            </span>
            <button
              id="logout-btn"
              className="btn btn-ghost btn-sm"
              onClick={logout}
              title="Sign out"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
