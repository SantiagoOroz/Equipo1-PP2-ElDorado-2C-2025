// Importamos más íconos
import React, { useState, useEffect, useRef } from "react";
import { SendHorizonal, Loader2, FileText, Globe, Mic, Volume2, Trash2 } from "lucide-react"; 

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  // --- Estados nuevos para Audio ---
  const [isRecording, setIsRecording] = useState(false);
  const [audioLoading, setAudioLoading] = useState(null); // Para el spinner de "Escuchar"
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => endRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(scrollToBottom, [messages]);

  // --- Función 1: Limpiar Chat ---
  const clearChat = () => {
    setMessages([]);
  };

  // --- Función 2: Enviar Mensaje (texto) ---
  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    // El mensaje de usuario no tiene fuentes
    const userMessage = { sender: "user", text: input, sources: null };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();

      // Guardamos la respuesta Y las fuentes en el estado
      const botMessage = {
        sender: "bot",
        text: data.reply || data.response || "Sin respuesta del servidor.",
        sources: data.sources || null, // Guardamos el objeto de fuentes
      };

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

  // --- Función 3: Iniciar Grabación (Whisper) ---
  const startRecording = async () => {
    if (mediaRecorderRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = handleStopRecording;
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error al acceder al micrófono:", err);
      alert("No se pudo acceder al micrófono. Por favor, revisá los permisos del navegador.");
    }
  };

  // --- Función 4: Detener Grabación y Transcribir (Whisper) ---
  const handleStopRecording = async () => {
    if (!mediaRecorderRef.current) return;
    
    mediaRecorderRef.current.stop();
    // Detener las pistas de audio para que el ícono de "grabando" desaparezca del navegador
    mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    mediaRecorderRef.current = null;
    setIsRecording(false);
    setLoading(true); // Usamos el spinner general

    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    try {
      const res = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      
      // ¡Clave! Ponemos el texto en el input para que el usuario lo revise
      if (data.text) {
        setInput(data.text);
      } else {
        throw new Error("Transcripción vacía");
      }

    } catch (err) {
      console.error("Error al transcribir:", err);
      alert("Hubo un error al transcribir el audio.");
    } finally {
      setLoading(false);
      audioChunksRef.current = [];
    }
  };

  // Función de palanca para el botón del micrófono
  const handleMicClick = () => {
    if (isRecording) {
      mediaRecorderRef.current.stop();
    } else {
      startRecording();
    }
  };

  // --- Función 5: Reproducir Audio (Edge-TTS) ---
  const playAudio = async (text, index) => {
    // Evitar múltiples reproducciones
    if (audioLoading !== null) return; 

    setAudioLoading(index); // Mostrar spinner en este mensaje
    try {
      const res = await fetch("/api/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          text: text, 
          voice: "es-AR-ElenaNeural" // Voz solicitada
        }),
      });

      if (!res.ok) throw new Error("Error en la respuesta del servidor");

      const blob = await res.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audio.play();
      audio.onended = () => setAudioLoading(null); // Ocultar spinner al terminar
      audio.onerror = () => {
        console.error("Error al reproducir audio");
        setAudioLoading(null);
      }

    } catch (err) {
      console.error("Error al sintetizar audio:", err);
      alert("No se pudo reproducir el audio.");
      setAudioLoading(null);
    }
  };

  return (
    <div className="flex flex-col w-full bg-gradient-to-b from-[#f8fafc] to-[#eef2f3] rounded-3xl shadow-2xl p-6 h-full backdrop-blur-md border border-gray-100">
      <div className="flex justify-between items-center mb-4 pb-2 border-b border-doradoLightBlue">
        <h1 className="text-2xl font-bold text-doradoOrange drop-shadow-sm">
          Asistente Técnico - El Dorado SRL
        </h1>
        <button
          onClick={clearChat}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition-colors duration-200 px-3 py-1 rounded-lg hover:bg-red-100"
          title="Limpiar historial de chat"
          disabled={messages.length === 0} // Deshabilitar si no hay nada que limpiar
        >
          <Trash2 size={16} />
          Limpiar
        </button>
      </div>

      {/* Zona de mensajes */}
      <div className="flex-1 overflow-y-auto pr-2 space-y-3">
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
              
              {/* --- Botón de Audio (Solo para el Bot) --- */}
              {msg.sender === "bot" && msg.text && (
                <div className="mt-2 pt-2 border-t border-white/20">
                  <button
                    onClick={() => playAudio(msg.text, i)}
                    disabled={audioLoading !== null} // Deshabilitar si otro audio está cargando/reproduciendo
                    className="flex items-center gap-1.5 text-xs text-white/70 hover:text-white transition-colors disabled:opacity-50"
                  >
                    {audioLoading === i ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Volume2 size={16} />
                    )}
                    {audioLoading === i ? "Cargando..." : "Escuchar"}
                  </button>
                </div>
              )}

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

        {/* Botón de Micrófono */}
        <button
          onClick={handleMicClick}
          className={`px-4 py-3 rounded-full text-white hover:scale-105 transition shadow-md disabled:opacity-50 ${
            isRecording ? "bg-red-600 hover:bg-red-700 animate-pulse" : "bg-gradient-to-r from-doradoLightBlue to-doradoBlue"
          }`}
          disabled={loading}
        >
          {isRecording ? <Loader2 size={18} className="animate-spin" /> : <Mic size={18} />}
        </button>

        {/* Input de texto */}
        <input
          type="text"
          className="flex-1 border border-gray-300 rounded-full px-4 py-3 focus:ring-2 focus:ring-doradoOrange outline-none text-gray-800 shadow-inner"
          placeholder="Escribí tu consulta..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !loading && sendMessage()} // Evita doble envío
          disabled={loading} // Deshabilitar input mientras carga
        />

        {/* Botón Enviar */}
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
