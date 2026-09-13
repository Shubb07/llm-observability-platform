import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

/**
 * main.tsx — the JavaScript entry point.
 *
 * This file is executed first when the browser loads the app.
 * It finds the <div id="root"> in index.html and mounts the React app into it.
 *
 * StrictMode:
 * A development-only wrapper that helps catch bugs by:
 *   - Rendering components twice (to catch side effects in render)
 *   - Detecting deprecated API usage
 *   - Logging additional warnings
 * It has ZERO effect in production builds. It's a free safety net.
 *
 * createRoot (React 18+):
 * The modern way to mount a React app. It enables concurrent features
 * (like transitions and Suspense) that the older ReactDOM.render() didn't support.
 */
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
