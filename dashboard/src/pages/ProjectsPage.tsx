/**
 * FILE: src/pages/ProjectsPage.tsx
 *
 * WEEK 1 STATUS: Placeholder page.
 *
 * Purpose right now: confirm that authentication, routing, AppLayout,
 * and ProtectedRoute all work together correctly. When a user logs in
 * successfully, they should land here and see this page inside the sidebar.
 *
 * Week 2 will replace this with the real Projects list (API call, project
 * cards, create project button, etc.).
 */

export default function ProjectsPage() {
  return (
    <>
      {/* Page header — same pattern every page will use */}
      <div className="page-header">
        <div>
          <h2>Projects</h2>
          <p>Your LLM observability projects</p>
        </div>
      </div>

      {/* Page body — empty state for now */}
      <div className="page-body">
        <div className="state-container">
          <div className="state-icon">📋</div>
          <p className="state-message">Projects coming in Week 2</p>
          <p className="state-hint">
            Authentication is working. The sidebar, protected routes, and JWT
            flow are all set up. Week 2 will add the real project list and
            create-project form.
          </p>
        </div>
      </div>
    </>
  );
}
