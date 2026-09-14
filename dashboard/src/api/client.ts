import axios from "axios";

function getCookie(name: string): string | null {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function deleteCookie(name: string): void {
  document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Strict`;
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

apiClient.interceptors.request.use((config) => {
  const token = getCookie("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      deleteCookie("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
