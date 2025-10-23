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
    <div
      className="flex"
      style={{
        height: "100vh",
        width: "100%",
        margin: 0,
        padding: 0,
        backgroundColor: "#f8f9fa",
      }}
    >
      {/* PANEL IZQUIERDO */}
      <div
        style={{
          width: "280px",
          backgroundColor: "#10172a",
          color: "#fff",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "20px 10px",
        }}
      >
        {/* LOGO CENTRADO */}
        <div style={{ textAlign: "center", marginBottom: "20px" }}>
          <img
            src="/img/logo_eldorado.jpg"
            alt="Logo El Dorado"
            style={{
              width: "120px",
              height: "auto",
            }}
          />
        </div>

        {/* SIDEBAR CON ACCIONES */}
        <Sidebar onAction={handleAction} />
      </div>

      {/* PANEL DERECHO - CHAT */}
      <div
        style={{
          flex: 1,
          padding: "15px 20px",
          backgroundColor: "#ffffff",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <Chat />
      </div>
    </div>
  );
}
