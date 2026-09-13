import axios from "axios";

/**
 * WHY axios.create()?
 * Instead of using bare `axios.get(...)` everywhere, we create a configured
 * instance. This means:
 *   - baseURL is set once here — all API functions just write "/api/v1/..."
 *   - Interceptors (see below) apply only to OUR requests, not to any other
 *     library that might also use Axios internally
 *
 * WHY VITE_API_URL?
 * Vite exposes environment variables prefixed with VITE_ to the browser at
 * build time via import.meta.env. The value comes from a .env file at the
 * root of the dashboard/ directory. If the backend moves, you change one line
 * in .env — not every API call. The fallback ensures zero-config local dev.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

/**
 * REQUEST INTERCEPTOR — attaches the JWT to every outgoing request.
 *
 * HOW IT WORKS:
 * Before Axios sends a request, this function runs. It reads the token from
 * localStorage and adds it to the Authorization header.
 *
 * WHY AN INTERCEPTOR (not adding the header in each API function)?
 * Without this, every function would need:
 *   const token = localStorage.getItem("token");
 *   headers: { Authorization: `Bearer ${token}` }
 * That's 2 lines repeated in every single API call. The interceptor does it
 * once, centrally, for every request automatically.
 *
 * The interceptor receives the Axios request config object, adds the header
 * if a token exists, and returns the (modified) config. Axios then sends it.
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * RESPONSE INTERCEPTOR — handles 401 Unauthorized globally.
 *
 * HOW IT WORKS:
 * The first function (identity) handles successful responses — just passes them through.
 * The second function handles errors. If the backend returns 401 (expired or invalid JWT),
 * we clear the stale token and redirect to /login.
 *
 * WHY GLOBAL 401 HANDLING?
 * The JWT expires after 24h (backend default). Without this, an expired token
 * would cause every single API call to fail with a cryptic error. The user would
 * see "Failed to load projects" / "Failed to load traces" with no explanation.
 * Instead: detect 401 → clear token → redirect to login → user understands.
 *
 * `return Promise.reject(error)` — we still reject the promise so TanStack Query
 * can set its error state for any OTHER errors (404, 500, validation, etc.).
 * We only handle 401 specially; everything else propagates normally.
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      // Hard redirect — clears all React state and starts fresh at /login
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
