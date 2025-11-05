import React from "react";
import { Loader2 } from 'lucide-react'; // 💡 Importar Loader2 para el spinner

// Aceptamos la nueva propiedad 'onLogout'
// 💡 Aceptamos la nueva propiedad 'isIndexing'
export default function Sidebar({ onAction, onLogout, isIndexing }) {
  const handleIndexClick = () => {
    if (window.confirm("¿Estás seguro de que quieres indexar? Esto borrará el índice anterior.")) {
      onAction("index");
    }
  };
    
  // Función para manejar las acciones con confirmación de bloqueo
  const handleSafeAction = (action, file = null) => {
    if (isIndexing) {
      alert("⚠️ El proceso de indexación está en curso. Por favor, espera a que termine.");
      return;
    }
    onAction(action, file);
  };
  return (
    <div className="bg-gradient-to-b from-doradoBlue to-[#0f172a] text-white w-72 p-6 flex flex-col justify-between shadow-2xl rounded-r-3xl">
      <div>
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/img/upscalemedia-transparent-achico.png"
            alt="Logo El Dorado"
            className="w-36 drop-shadow-lg transition-transform hover:scale-105"
          />
        </div>

        <h2 className="text-xl font-bold mb-6 text-center text-doradoOrange">
          Gestión de Archivos
        </h2>

        {/* Botones principales */}
        <div className="flex flex-col gap-3">
          <label className="cursor-pointer bg-white text-doradoBlue px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 shadow-sm transition">
            Seleccionar PDF
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => handleSafeAction("upload", e.target.files[0])}
              className="hidden"
              disabled={isIndexing}
            />
          </label>

          <button
            onClick={handleIndexClick}
            className={`bg-gradient-to-r from-doradoLightBlue to-doradoBlue px-4 py-2 rounded-lg text-sm font-medium shadow-md transition flex items-center justify-center gap-2 ${isIndexing ? 'opacity-50 cursor-not-allowed' : 'hover:from-doradoOrange hover:to-orange-500'}`}
            disabled={isIndexing} // 💡 Deshabilitar durante la indexación
          >
            {isIndexing ? (
              <>
                <Loader2 className="animate-spin" size={18} /> Indexando...
              </>
            ) : (
              "📑 Indexar Conocimiento"
            )}
          </button>

          <button
            onClick={() => handleSafeAction("export")}
            className={`bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition ${isIndexing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-500'}`}
            disabled={isIndexing} // 💡 Deshabilitar durante la indexación
          >
            ⬇️ Exportar Índice
          </button>

          <label className={`cursor-pointer px-4 py-2 rounded-lg text-sm font-medium text-center transition ${isIndexing ? 'bg-gray-700 opacity-50 cursor-not-allowed' : 'bg-gray-700 hover:bg-gray-600'}`}>
            ⬆️ Importar Índice
            <input
              type="file"
              accept=".json, .zip, application/json, application/zip"
              onChange={(e) => onAction("import", e.target.files[0])}
              className="hidden"
            />
          </label>

          <button
            onClick={() => {
              if (window.confirm("⚠️ ¿Estás seguro de borrar toda la base de datos vectorial?")) {
                handleSafeAction("clear");
              }
            }}
            className={`bg-red-600 px-4 py-2 rounded-lg text-sm font-medium shadow-md transition mt-2 ${isIndexing ? 'opacity-50 cursor-not-allowed' : 'hover:bg-red-700'}`}
            disabled={isIndexing} // 💡 Deshabilitar
          >
            🗑️ Limpiar Colección
          </button>

          {/* Botón para "cerrar sesión" u ocultar el panel */}
          <button
            onClick={onLogout}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium shadow-md transition mt-4"
          >
            🔒 Ocultar Panel
          </button>
        </div>
      </div>
      <div>
    {/* ... (Tu contenido anterior) ... */}

    {/* Enlace al Manual de Usuario */}
    <div className="text-center mb-1">
      <a 
        href="https://cristiancouto.github.io/eldoradosrl.github.io/#/guia-usuario"
        target="_blank" // Esto es buena práctica para abrir enlaces externos en una pestaña nueva
        rel="noopener noreferrer" // Mejora la seguridad y rendimiento
        className="text-sm text-blue-500 hover:text-blue-700 font-medium" // Estilo diferente al footer
      >
        📒 Manual de usuario
      </a>
    </div>

    {/* Footer de Copyright (el original) */}
    <footer className="text-center text-xs text-gray-400 mt-6">
      © 2025 El Dorado SRL
    </footer>
</div>
    </div>
  );
}
