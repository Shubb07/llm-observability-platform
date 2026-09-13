// These interfaces mirror the backend's Pydantic schemas in app/schemas/auth.py
// EXACTLY. Do not add fields that don't exist in the backend response.

/**
 * Returned by POST /api/v1/auth/login
 * The JWT the frontend stores in localStorage.
 */
export interface Token {
  access_token: string;
  token_type: string; // always "bearer" per the backend schema
}

/**
 * Returned by POST /api/v1/auth/register and GET /api/v1/auth/me
 * The basic user identity. No password, no sensitive fields.
 */
export interface UserOut {
  id: string;
  email: string;
}
