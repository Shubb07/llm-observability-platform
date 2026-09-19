import { useQuery } from "@tanstack/react-query";
import { checkHealth } from "../../api/health";

export default function SidebarStatus() {
  const { data: healthy, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: checkHealth,
    refetchInterval: 15_000,
    retry: false,
  });

  const state = isLoading ? "checking" : healthy ? "up" : "down";
  const label = state === "checking" ? "Checking…" : state === "up" ? "Operational" : "Unreachable";

  return (
    <div className="sidebar-status">
      <span className={`sidebar-status-dot sidebar-status-dot-${state}`} />
      <div>
        <p className="sidebar-status-label">Backend API</p>
        <p className={`sidebar-status-value sidebar-status-value-${state}`}>{label}</p>
      </div>
    </div>
  );
}
