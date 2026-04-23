import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";
import { applyTheme, getInitialTheme } from "./theme";

const el = document.getElementById("root");
if (!el) throw new Error("Root element missing");

applyTheme(getInitialTheme());

createRoot(el).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
