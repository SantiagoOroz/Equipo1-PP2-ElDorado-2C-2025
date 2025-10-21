import React, { useState, useEffect, useRef } from "react";
import { SendHorizonal, Loader2 } from "lucide-react";

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
    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      const botMessage = {
        sender: "bot",
        text: data.reply || data.response || "Sin respuesta del servidor.",
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Error al conectar con el backend." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full bg-gradient-to-b from-[#f8fafc] to-[#eef2f3] rounded-3xl shadow-2xl p-6 h-[90vh] backdrop-blur-md border border-gray-100">
      <h1 className="text-2xl font-bold text-doradoOrange mb-4 border-b border-doradoLightBlue pb-2 drop-shadow-sm">
        Asistente Técnico - El Dorado SRL
      </h1>

      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto pr-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex my-3 transition-all ${
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
              {msg.text}
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
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className="bg-gradient-to-r from-doradoOrange to-orange-500 text-white px-6 py-3 rounded-full hover:scale-105 transition flex items-center gap-2 shadow-md"
        >
          <SendHorizonal size={18} /> Enviar
        </button>
      </div>
    </div>
  );
}
