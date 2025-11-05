
import React from "react";
import AppLayout from "./components/AppLayout";

// Silencia ResizeObserver loop errors en consola (solo en desarrollo)
const resizeObserverErr = /ResizeObserver loop completed|ResizeObserver loop limit exceeded/;
window.addEventListener("error", (e) => {
  if (resizeObserverErr.test(e.message)) {
    e.stopImmediatePropagation();
  }
});
window.addEventListener("unhandledrejection", (e) => {
  if (resizeObserverErr.test(e.reason)) {
    e.preventDefault();
  }
});


function App() {
  return <AppLayout />;
}

export default App;
