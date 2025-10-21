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
    <div className="flex flex-col w-full bg-doradoWhite rounded-xl shadow-lg p-6 h-[90vh]">
      <h1 className="text-2xl font-semibold text-doradoOrange mb-4 border-b border-doradoLightBlue pb-2">
        Asistente Técnico - El Dorado SRL
      </h1>

      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto will-change-scroll pr-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex my-2 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`px-4 py-2 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-sm ${
                msg.sender === "user"
                  ? "bg-doradoOrange text-white rounded-br-none"
                  : "bg-doradoLightBlue text-white rounded-bl-none"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-doradoLightBlue text-center my-2 flex justify-center items-center gap-2">
            <Loader2 className="animate-spin" size={18} /> Procesando...
          </div>
        )}
        <div ref={endRef}></div>
      </div>

      {/* Input de usuario */}
      <div className="flex gap-2 mt-4">
        <input
          type="text"
          className="flex-1 border border-gray-300 rounded-xl px-4 py-2 focus:ring-2 focus:ring-doradoOrange outline-none text-gray-800"
          placeholder="Escribí tu consulta..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className="bg-doradoOrange text-white px-5 py-2 rounded-xl hover:bg-orange-500 flex items-center gap-2 shadow-md transition"
        >
          <SendHorizonal size={18} /> Enviar
        </button>
      </div>
    </div>
  );
}
