import React from "react";
import Sidebar from "./Sidebar";
import Chat from "./Chat";

export default function AppLayout() {
  const handleAction = async (action, file) => {
    const routes = {
      index: "/api/index",
      embed: "/api/embed",
      clear: "/api/clear",
      export: "/api/export",
      import: "/api/import",
      upload: "/upload",
    };

    const url = routes[action];
    if (!url) return;

    const options = { method: "POST" };
    const formData = new FormData();

    if (file) formData.append("file", file);
    if (["upload", "import"].includes(action)) options.body = formData;
    if (["index", "embed", "clear"].includes(action)) options.headers = { "Content-Type": "application/json" };

    try {
      const res = await fetch(url, options);
      const data = await res.json();
      alert(data.msg || data.message || "Operación completada.");
    } catch (error) {
      alert("⚠️ Error al conectar con el servidor Flask.");
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar onAction={handleAction} />
      <div className="flex-1 p-4 bg-doradoLight">
        <Chat />
      </div>
    </div>
  );
}
