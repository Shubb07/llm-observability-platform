/** Formatter utilities for displaying trace data in human-readable format. */

/**
 * Format latency: backend stores milliseconds as a float.
 * Under 1000ms → show "423 ms"
 * Over 1000ms → show "1.42 s"
 */
export function formatLatency(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }
  return `${(ms / 1000).toFixed(2)} s`;
}

/**
 * Format cost: backend stores USD as a float (e.g. 0.00032).
 * Very small values get more decimal places for readability.
 */
export function formatCost(usd: number): string {
  if (usd === 0) return "$0.00";
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(4)}`;
}

/**
 * Format token count with commas for readability.
 * e.g. 12345 → "12,345"
 */
export function formatTokens(count: number): string {
  return count.toLocaleString();
}

/**
 * Format an ISO datetime string into a human-readable local time.
 * e.g. "2026-09-08T10:30:00Z" → "Sep 8, 2026, 4:00 PM" (in user's timezone)
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format a datetime as a relative time for table display.
 * e.g. "2 minutes ago", "3 hours ago", "Sep 8"
 */
export function formatRelativeDate(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
