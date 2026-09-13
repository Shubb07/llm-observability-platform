import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./routes/ProtectedRoute";
import AppLayout from "./components/layout/AppLayout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ProjectsPage from "./pages/ProjectsPage";

/**
 * QueryClient — the in-memory cache that TanStack Query uses.
 *
 * WHY OUTSIDE THE COMPONENT?
 * If we wrote `const queryClient = new QueryClient()` inside App(), it would
 * create a NEW QueryClient on every render, destroying the cache each time.
 * Placing it at module level means it's created once when the file is loaded
 * and shared for the entire app lifetime.
 *
 * defaultOptions:
 *   retry: 1 — if a request fails, TanStack Query retries it once automatically
 *              before marking it as an error. Useful for transient network errors.
 *   staleTime: 30_000 — data is considered "fresh" for 30 seconds after fetching.
 *              During this window, navigating to a page shows cached data instantly
 *              (no loading spinner) instead of refetching. After 30s, data is
 *              "stale" and will be refetched in the background on next access.
 *   refetchOnWindowFocus: false — by default, TanStack Query refetches when you
 *              tab back to the window. For a developer tool, this is more annoying
 *              than helpful, so we disable it.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * App — the root component that sets up:
 *   1. BrowserRouter — enables React Router (URL-based navigation)
 *   2. QueryClientProvider — shares the QueryClient cache with all components
 *   3. AuthProvider — shares auth state (token, user, login, logout) with all components
 *   4. Routes — maps URLs to pages
 *
 * PROVIDER NESTING ORDER MATTERS:
 *   BrowserRouter must wrap everything that uses React Router (useNavigate, useParams).
 *   QueryClientProvider must wrap everything that uses TanStack Query (useQuery, useMutation).
 *   AuthProvider is inside both because AuthContext uses navigate (React Router)
 *   and internally uses effects that may use React Router.
 *
 * ROUTING STRUCTURE:
 *   /login, /register — public, no auth required
 *   <ProtectedRoute> — layout route that checks auth
 *     /projects, /projects/new, /projects/:id/traces, etc. — protected
 *   * (catch-all) — redirects to /projects
 */
export default function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/**
             * Protected routes — two layers of nesting:
             *
             * Layer 1: ProtectedRoute — auth guard.
             *   Checks token. If missing → redirect to /login.
             *   If present → render <Outlet /> (which is AppLayout).
             *
             * Layer 2: AppLayout — the sidebar shell.
             *   Draws the sidebar + main content area.
             *   Renders <Outlet /> inside main content (which is the page).
             *
             * Layer 3: Individual page routes.
             *   The actual page content (ProjectsPage, TracesPage, etc.)
             *
             * Route structure:
             *   /projects           → ProjectsPage   (Week 1 placeholder, real in Week 2)
             *   /projects/new       → placeholder     (Week 2)
             *   /projects/:id/traces → placeholder    (Week 3)
             */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                {/* Week 1 — Projects placeholder (real list in Week 2) */}
                <Route path="/projects" element={<ProjectsPage />} />

                {/* Week 2 — Create project (not built yet) */}
                <Route
                  path="/projects/new"
                  element={
                    <div className="page-body">
                      <div className="state-container">
                        <div className="state-icon">🚧</div>
                        <p className="state-message">Coming in Week 2</p>
                      </div>
                    </div>
                  }
                />

                {/* Week 3 — Trace Explorer (not built yet) */}
                <Route
                  path="/projects/:projectId/traces"
                  element={
                    <div className="page-body">
                      <div className="state-container">
                        <div className="state-icon">🚧</div>
                        <p className="state-message">Coming in Week 3</p>
                      </div>
                    </div>
                  }
                />
              </Route>
            </Route>

            {/* Catch-all: unknown URLs go to /projects */}
            <Route path="*" element={<Navigate to="/projects" replace />} />
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}
