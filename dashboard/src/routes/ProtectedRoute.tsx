import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute() {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="state-container" style={{ minHeight: "100vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
