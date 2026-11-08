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
    // A 401 only means "your session is no longer valid" if the request
    // was actually sent as an authenticated one - login/register calls
    // never carry a token, so a wrong-password 401 from the login form
    // itself used to hit this same branch, wiping the form and bouncing
    // back to /login before React ever rendered the "incorrect password"
    // error the mutation already had.
    const hadToken = Boolean(error.config?.headers?.Authorization);
    if (error.response?.status === 401 && hadToken) {
      deleteCookie("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
