import React from "react";

export default function Sidebar({ onAction }) {
  return (
    <div className="bg-gradient-to-b from-doradoBlue to-[#0f172a] text-white w-72 p-6 flex flex-col justify-between shadow-2xl rounded-r-3xl">
      <div>
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/img/logo_eldorado.png"
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
              onChange={(e) => onAction("upload", e.target.files[0])}
              className="hidden"
            />
          </label>

          <button
            onClick={() => onAction("index")}
            className="bg-gradient-to-r from-doradoLightBlue to-doradoBlue hover:from-doradoOrange hover:to-orange-500 px-4 py-2 rounded-lg text-sm font-medium shadow-md transition"
          >
            📑 Indexar PDFs
          </button>

          <button
            onClick={() => onAction("embed")}
            className="bg-gradient-to-r from-doradoOrange to-orange-500 hover:from-orange-400 hover:to-doradoOrange px-4 py-2 rounded-lg text-sm font-medium text-white shadow-md transition"
          >
            🧠 Generar Embeddings
          </button>

          <button
            onClick={() => onAction("export")}
            className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition"
          >
            ⬇️ Exportar Índice
          </button>

          <label className="cursor-pointer bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium text-center transition">
            ⬆️ Importar Índice
            <input
              type="file"
              accept=".json"
              onChange={(e) => onAction("import", e.target.files[0])}
              className="hidden"
            />
          </label>

          <button
            onClick={() => onAction("clear")}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg text-sm font-medium shadow-md transition mt-2"
          >
            🗑️ Limpiar Colección
          </button>
        </div>
      </div>

      <footer className="text-center text-xs text-gray-400 mt-6">
        © 2025 El Dorado SRL
      </footer>
    </div>
  );
}
