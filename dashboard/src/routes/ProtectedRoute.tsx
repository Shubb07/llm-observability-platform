import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * HOW PROTECTED ROUTES WORK IN REACT ROUTER V6
 *
 * In React Router v6, a "layout route" is a route with no path that renders
 * an <Outlet />. All child routes render inside that <Outlet />.
 *
 * We use this pattern:
 *
 *   <Route element={<ProtectedRoute />}>      ← this component (no path)
 *     <Route path="/projects" element={...} />  ← child routes
 *     <Route path="/projects/:id/traces" element={...} />
 *   </Route>
 *
 * When React Router tries to match /projects:
 *   1. It renders ProtectedRoute first
 *   2. If authenticated → ProtectedRoute renders <Outlet /> → /projects page renders inside it
 *   3. If not authenticated → ProtectedRoute renders <Navigate to="/login" /> → redirect
 *
 * This means every child route is automatically protected — you don't have to add
 * auth checks to each individual page.
 *
 * WHY `replace`?
 * <Navigate replace> replaces the current history entry instead of pushing a new one.
 * Without it: the user's history looks like [/projects, /login].
 * Clicking Back on the login page would go back to /projects → ProtectedRoute → redirect → /login again.
 * With replace: the /projects entry is replaced by /login, so Back goes to wherever
 * the user was before they tried to access /projects.
 *
 * WHY isLoading CHECK?
 * On first load, if there's a token in localStorage, AuthContext calls GET /auth/me
 * to validate it. While that's in flight, we don't know yet if the user is
 * authenticated or not. If we immediately check `!token`, we'd briefly redirect
 * to /login even for valid tokens. Showing a blank screen (or spinner) while
 * validating avoids this "flash of login page" problem.
 */
export default function ProtectedRoute() {
  const { token, isLoading } = useAuth();

  /**
   * Still validating the stored token — show a full-page spinner.
   *
   * WHY NOT null?
   * Returning null gives the user a completely blank screen for however long
   * the GET /auth/me request takes (could be 100ms, could be 1s on a slow
   * connection). A spinner communicates "the app is working" so the user
   * doesn't think it's broken or frozen.
   *
   * The spinner and state-container classes are defined in index.css.
   */
  if (isLoading) {
    return (
      <div className="state-container" style={{ minHeight: "100vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  // No token (or token was cleared by 401 interceptor) → go to login.
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Authenticated — render the child route's page inside <Outlet />.
  return <Outlet />;
}
