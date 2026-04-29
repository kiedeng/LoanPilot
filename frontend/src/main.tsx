import React from "react";
import ReactDOM from "react-dom/client";
import { injectStyles } from "@a2ui/react/styles";
import App from "./App";
import "./styles.css";

injectStyles();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
