import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

/**
 * FILE: src/components/layout/AppLayout.tsx
 *
 * PURPOSE:
 * The persistent shell that wraps every protected page. It renders:
 *   - A sidebar on the left (brand, navigation, user info, logout)
 *   - A main area on the right where the current page renders
 *
 * HOW IT WORKS WITH REACT ROUTER:
 * In App.tsx, AppLayout is the `element` of a parent <Route> with no path:
 *
 *   <Route element={<AppLayout />}>
 *     <Route path="/projects" element={<ProjectsPage />} />
 *   </Route>
 *
 * When React Router matches /projects:
 *   1. It renders AppLayout (sidebar + layout)
 *   2. Inside AppLayout, <Outlet /> renders ProjectsPage
 *
 * This means the sidebar is drawn ONCE and stays on screen while you
 * navigate between pages — only the main content area changes.
 *
 * WHY A SEPARATE LAYOUT COMPONENT?
 * The alternative is: every page renders its own sidebar. That means:
 *   - Copy-pasting sidebar JSX into 5–10 pages
 *   - Updating the sidebar in 5–10 places when it changes
 * Layout routes eliminate this duplication.
 */

export default function AppLayout() {
  /**
   * useAuth() — reads from AuthContext.
   * We need:
   *   - `user.email` to display in the sidebar footer
   *   - `logout` to call when the user clicks "Sign out"
   */
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      {/* ----------------------------------------------------------------
          SIDEBAR
          Fixed-width left panel. Contains: brand, nav links, user + logout.
          The CSS for all these classes (.sidebar, .sidebar-brand, etc.)
          is already defined in index.css.
      ---------------------------------------------------------------- */}
      <aside className="sidebar">

        {/* Brand / logo area */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">📡</div>
          <span className="sidebar-brand-name">LLM Observability</span>
        </div>


        <nav className="sidebar-section">
          <p className="sidebar-section-label">Navigation</p>
          <div className="sidebar-nav">
            {/**
             * NavLink vs Link:
             * Both navigate to a URL. NavLink additionally adds an `active`
             * CSS class when the current URL matches the `to` prop. This lets
             * us style the active nav item differently (see .sidebar-nav-link.active
             * in index.css — it gets the indigo highlight).
             *
             * `end` prop on the /projects link: without `end`, /projects would
             * be considered "active" on /projects/new and /projects/:id/traces
             * too (because they all start with /projects). `end` makes it only
             * active when the path is exactly /projects.
             */}
            <NavLink
              to="/projects"
              end
              className="sidebar-nav-link"
            >
              📋 Projects
            </NavLink>

          </div>
        </nav>

        {/* User info + logout — pinned to the bottom of the sidebar */}
        <div className="sidebar-footer">
          <div className="sidebar-user">
            {/**
             * user?.email — optional chaining because user is null
             * while the initial /auth/me request is in flight.
             * Once it resolves, user is populated and the email appears.
             * In practice this is only null for a split second after login.
             */}
            <span className="sidebar-user-email">
              {user?.email ?? "Loading…"}
            </span>

            {/**
             * Logout button.
             *
             * WHAT logout() does (from AuthContext):
             *   1. localStorage.removeItem("token") — clears persisted token
             *   2. setToken(null) — clears React state
             *   3. setUser(null) — clears user state
             *
             * After calling logout(), the token state in AuthContext becomes null.
             * ProtectedRoute checks `!token` → renders <Navigate to="/login" />.
             * The redirect happens automatically — we don't need to call navigate().
             */}
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

      {/* MAIN CONTENT AREA — <Outlet /> renders the active child page here */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
