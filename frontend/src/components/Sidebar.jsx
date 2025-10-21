import React from "react";

export default function Sidebar({ onAction }) {
  return (
    <div className="bg-doradoBlue text-white w-64 p-5 flex flex-col justify-between">
      <div>
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img
            src="/img/logo_eldorado.png"
            alt="Logo El Dorado"
            className="w-32 rounded-lg shadow-md"
          />
        </div>

        <h2 className="text-lg font-semibold mb-4 text-center text-doradoOrange">
          Gestión de Archivos
        </h2>

        {/* Botones principales */}
        <div className="flex flex-col gap-2">
          <label className="cursor-pointer bg-white text-doradoBlue px-3 py-2 rounded-md text-sm hover:bg-gray-100">
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
            className="bg-doradoLightBlue hover:bg-doradoOrange hover:text-white transition px-3 py-2 rounded-md text-sm"
          >
            📑 Indexar PDFs
          </button>

          <button
            onClick={() => onAction("embed")}
            className="bg-doradoOrange hover:bg-orange-500 text-white px-3 py-2 rounded-md text-sm"
          >
            🧠 Generar Embeddings
          </button>

          <button
            onClick={() => onAction("export")}
            className="bg-gray-500 hover:bg-gray-600 px-3 py-2 rounded-md text-sm"
          >
            ⬇️ Exportar Índice
          </button>

          <label className="cursor-pointer bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-md text-sm text-center">
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
            className="bg-red-600 hover:bg-red-700 px-3 py-2 rounded-md text-sm mt-2"
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
