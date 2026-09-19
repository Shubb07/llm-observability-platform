import axios from "axios";

const HEALTH_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000") + "/health";

export async function checkHealth(): Promise<boolean> {
  const response = await axios.get(HEALTH_URL, { timeout: 4000 });
  return response.status === 200;
}
