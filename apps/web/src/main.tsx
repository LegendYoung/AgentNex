import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import "../../../packages/ui/src/styles/globals.css"
import "./i18n"
import { App } from "./App.tsx"
import { ErrorBoundary } from "./ErrorBoundary.tsx"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>
)