import axios from "axios";

/**
 * Extracts a human-readable error message from an Axios error.
 *
 * WHY THIS UTILITY?
 * When an API call fails, Axios gives you an AxiosError object with:
 *   error.response.data.detail  — FastAPI puts validation/auth errors here
 *   error.response.status       — HTTP status code (400, 401, 422, 500, etc.)
 *   error.message               — Axios's own message ("Request failed with status 422")
 *
 * We never want to show users the raw error object or Axios's technical messages.
 * This function extracts the most useful human-readable string.
 *
 * FastAPI returns errors as: { "detail": "Email already registered" }
 * For 422 Unprocessable Entity (validation), detail can be an array of objects —
 * in that case we stringify the first message.
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    // FastAPI validation errors (422) have detail as an array of objects
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      return first.msg ?? "Validation error. Check your inputs.";
    }

    // Fallback to HTTP status text
    if (error.response?.statusText) {
      return error.response.statusText;
    }
  }

  return "Something went wrong. Please try again.";
}
