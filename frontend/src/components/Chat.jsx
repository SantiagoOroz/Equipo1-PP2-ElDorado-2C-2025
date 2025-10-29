// {/* ---------MODIFICACIÓN INICIA-------- */}
// Importamos más íconos
import React, { useState, useEffect, useRef } from "react";
import { SendHorizonal, Loader2, FileText, Globe } from "lucide-react"; 
// {/* ---------MODIFICACIÓN FINALIZA-------- */}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  const scrollToBottom = () => endRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    // {/* ---------MODIFICACIÓN INICIA-------- */}
    // El mensaje de usuario no tiene fuentes
    const userMessage = { sender: "user", text: input, sources: null };
    // {/* ---------MODIFICACIÓN FINALIZA-------- */}
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();

      // {/* ---------MODIFICACIÓN INICIA-------- */}
      // Guardamos la respuesta Y las fuentes en el estado
      const botMessage = {
        sender: "bot",
        text: data.reply || data.response || "Sin respuesta del servidor.",
        sources: data.sources || null, // Guardamos el objeto de fuentes
      };
      // {/* ---------MODIFICACIÓN FINALIZA-------- */}
      setMessages((prev) => [...prev, botMessage]);

    } catch {
      setMessages((prev) => [
        ...prev,
        { 
          sender: "bot", 
          text: "⚠️ Error al conectar con el backend.", 
          sources: null // El mensaje de error no tiene fuentes
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full bg-gradient-to-b from-[#f8fafc] to-[#eef2f3] rounded-3xl shadow-2xl p-6 h-full backdrop-blur-md border border-gray-100">
      <h1 className="text-2xl font-bold text-doradoOrange mb-4 border-b border-doradoLightBlue pb-2 drop-shadow-sm">
        Asistente Técnico - El Dorado SRL
      </h1>

      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-3">
        {/* {/* ---------MODIFICACIÓN INICIA-------- */}
        {/* Agregamos un mensaje de bienvenida inicial */}
        {messages.length === 0 && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-md bg-gradient-to-r from-doradoLightBlue to-doradoBlue text-white rounded-bl-none">
              ¡Hola! Soy un asistente técnico especializado en el sistema de gestión de calidad de El Dorado SRL. Estoy aquí para ayudarte con cualquier pregunta o duda que tengas relacionada con los documentos y procedimientos de la empresa. ¿En qué puedo ayudarte?
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex transition-all ${
              msg.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`px-4 py-3 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-md transform hover:scale-[1.02] transition-all duration-200 ${
                msg.sender === "user"
                  ? "bg-gradient-to-r from-doradoOrange to-orange-500 text-white rounded-br-none"
                  : "bg-gradient-to-r from-doradoLightBlue to-doradoBlue text-white rounded-bl-none"
              }`}
            >
              {/* 1. El texto de la respuesta */}
              {msg.text}

              {/* 2. Renderizado de las fuentes (si existen) */}
              {msg.sender === "bot" && msg.sources && (
                <div className="mt-3 pt-3 border-t border-white/30 text-xs opacity-90">
                  <strong className="font-bold">Fuentes:</strong>
                  <ul className="list-none pl-0 mt-1 space-y-2">
                    
                    {/* Renderizar fuentes de PDFs */}
                    {msg.sources.pdfs && msg.sources.pdfs.length > 0 &&
                      msg.sources.pdfs.map((source, idx) => (
                        <li key={`pdf-${idx}`}>
                          <strong className="flex items-center gap-1.5">
                            <FileText size={14} />
                            {source.name} (Pág: {source.page})
                          </strong>
                          {/* 💡 Condición para mostrar el extracto/blockquote */}
                          {source.extract && source.extract.length > 3 && ( 
                            <blockquote className="border-l-2 border-white/50 pl-2 ml-1 italic text-white/80 mt-1">
                              {source.extract}
                            </blockquote>
                          )}
                        </li>
                      ))}
                    
                    {/* Renderizar fuentes de Wiki */}
                    {msg.sources.wiki && msg.sources.wiki.length > 0 &&
                      msg.sources.wiki.map((source, idx) => (
                        <li key={`wiki-${idx}`}>
                          <strong className="flex items-center gap-1.5">
                            <Globe size={14} />
                            {source.name} (Wiki)
                          </strong>
                          {/* 💡 Condición para mostrar el extracto/blockquote */}
                          {source.extract && source.extract.length > 3 && (
                            <blockquote className="border-l-2 border-white/50 pl-2 ml-1 italic text-white/80 mt-1">
                              {source.extract}
                            </blockquote>
                          )}
                        </li>
                      ))}
                  </ul>
                </div>
              )}

            </div>
          </div>
        ))}

        {loading && (
          <div className="text-doradoLightBlue text-center my-3 flex justify-center items-center gap-2">
            <Loader2 className="animate-spin" size={18} /> Procesando...
          </div>
        )}
        <div ref={endRef}></div>
      </div>

      {/* Input */}
      <div className="flex gap-2 mt-4">
        <input
          type="text"
          className="flex-1 border border-gray-300 rounded-full px-4 py-3 focus:ring-2 focus:ring-doradoOrange outline-none text-gray-800 shadow-inner"
          placeholder="Escribí tu consulta..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !loading && sendMessage()} // Evita doble envío
          disabled={loading} // Deshabilitar input mientras carga
        />
        <button
          onClick={sendMessage}
          className="bg-gradient-to-r from-doradoOrange to-orange-500 text-white px-6 py-3 rounded-full hover:scale-105 transition flex items-center gap-2 shadow-md disabled:opacity-50"
          disabled={loading} // Deshabilitar botón mientras carga
        >
          <SendHorizonal size={18} /> Enviar
        </button>
      </div>
    </div>
  );
}
