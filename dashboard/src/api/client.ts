import axios from "axios";

declare module "axios" {
  export interface AxiosRequestConfig {
    // Set on login/register calls - a wrong-password 401 from the login
    // form itself is not "your session expired," so it must not trigger
    // the global redirect below. See auth.ts.
    skipAuthRedirect?: boolean;
  }
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  // The access token lives in an HttpOnly cookie set by the backend
  // (POST /auth/login, /auth/register's follow-up login) - this instance
  // never reads or attaches it itself. withCredentials just tells the
  // browser to send/accept that cookie on cross-origin requests, same as
  // it already would for a same-origin one.
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.skipAuthRedirect) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
