import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Chat from "./Chat";

// {/* ---------MODIFICACIÓN INICIA-------- */}
// --- Define tu contraseña de administrador aquí ---
const ADMIN_PASS = "eldorado123"; // ¡Cambia esto por tu palabra clave!

// --- Componente de Login (solo visible en este archivo) ---
function AdminLogin({ onLoginSuccess }) {
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    if (password === ADMIN_PASS) {
      onLoginSuccess();
    } else {
      alert("❌ Contraseña incorrecta.");
      setPassword("");
    }
  };

  // Usamos el mismo estilo que el Sidebar para que no haya saltos visuales
  return (
    <div className="bg-gradient-to-b from-doradoBlue to-[#0f172a] text-white w-72 p-6 flex flex-col justify-between shadow-2xl rounded-r-3xl">
      <div>
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/img/upscalemedia-transparent-achico.png"
            alt="Logo El Dorado"
            className="w-36 drop-shadow-lg"
          />
        </div>
        <h2 className="text-xl font-bold mb-6 text-center text-doradoOrange">
          Acceso Técnico
        </h2>
        <div className="flex flex-col gap-3">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyUp={(e) => e.key === 'Enter' && handleLogin()}
            placeholder="Contraseña"
            className="bg-white text-gray-900 px-4 py-2 rounded-lg text-sm"
          />
          <button
            onClick={handleLogin}
            className="bg-gradient-to-r from-doradoLightBlue to-doradoBlue hover:from-doradoOrange hover:to-orange-500 px-4 py-2 rounded-lg text-sm font-medium shadow-md transition"
          >
            Acceder
          </button>
        </div>
      </div>
      <footer className="text-center text-xs text-gray-400 mt-6">
        © 2025 El Dorado SRL
      </footer>
    </div>
  );
}


export default function AppLayout() {

  // Estado para controlar si el admin está logueado
  const [isAdmin, setIsAdmin] = useState(false);

  const [isIndexing, setIsIndexing] = useState(false);

  const handleAction = async (action, file) => {
    const routes = {
      index: "/api/index",
      clear: "/api/clear",
      export: "/api/export",
      import: "/api/import",
      upload: "/upload",
    };

    // Usamos la ruta relativa (correcta para tu proxy)
    const url = routes[action];
    if (!url) return;

    // 💡 Si la acción es indexar, activamos la bandera y notificamos
    if (action === "index") {
      setIsIndexing(true);
      alert("⏳ Iniciando indexación de PDFs y Wiki. Esto puede tardar varios minutos...");
    }

    const options = { method: "POST" };
    const formData = new FormData();

    if (file) formData.append("file", file);
    if (["upload", "import"].includes(action)) options.body = formData;
    
    // 'index' y 'clear' sí
    if (["index", "clear"].includes(action)) {
      options.headers = { "Content-Type": "application/json" };
    }
    
    // 'export' es un GET
    if (action === "export") {
        options.method = "GET";
    }

    try {
      const res = await fetch(url, options);
      
      // Lógica especial para exportar, que devuelve un archivo
      if (action === "export") {
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.error || "Error al exportar");
        }
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = "chroma_index.zip"; // Exportamos el zip de chroma
        document.body.appendChild(a);
        a.click();
        a.remove();
        alert("📦 Índice exportado correctamente.");
        return;
      }
      
      const data = await res.json();
      
      if (!res.ok) {
          throw new Error(data.error || data.msg || "Error en la operación");
      }
      
      alert(data.msg || data.message || "Operación completada.");
    } catch (error) {
      console.error("Error en handleAction:", error);
      alert(`⚠️ Error: ${error.message}`);
    } finally {
      // 💡 Desactivar la bandera al finalizar (éxito o error)
      if (action === "index") {
        setIsIndexing(false);
      }
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Renderizado condicional: 
          Si 'isAdmin' es true, muestra Sidebar. 
          Si es false, muestra AdminLogin. 
      */}
      {isAdmin ? (
        <Sidebar 
          onAction={handleAction} 
          onLogout={() => setIsAdmin(false)} // Pasamos la función de logout
          isIndexing={isIndexing} // 💡 PASAR EL ESTADO A SIDEBAR
        />
      ) : (
        <AdminLogin 
          onLoginSuccess={() => setIsAdmin(true)} // Pasamos la función de login
        />
      )}

      <div className="flex-1 p-4 bg-doradoLight">
        <Chat />
      </div>
    </div>
  );
}