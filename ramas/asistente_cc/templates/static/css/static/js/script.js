// Escuchar clicks en los botones
document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("clear-btn").addEventListener("click", clearChat);

async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  addMessage("Tú", message);
  input.value = "";

  // Mostrar indicador de "escribiendo..."
  const typingId = addMessage("Chatbot", "⌛ Escribiendo...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await response.json();

    // Reemplazar el mensaje "Escribiendo..." por la respuesta real
    updateMessage(typingId, `💬 ${data.response}`);

    // Mostrar fuentes si existen
    if (data.sources) {
      let fuentes = "";
      if (data.sources.pdfs && data.sources.pdfs.length > 0) {
        fuentes += `<p><b>PDFs:</b> ${data.sources.pdfs.join(", ")}</p>`;
      }
      if (data.sources.wiki && data.sources.wiki.length > 0) {
        fuentes += `<p><b>Wiki:</b> ${data.sources.wiki.join(", ")}</p>`;
      }
      if (fuentes) {
        addMessage("Fuentes", fuentes);
      }
    }

  } catch (error) {
    updateMessage(typingId, "⚠️ Error de conexión con el servidor.");
  }
}

// Agregar mensaje al chat
function addMessage(sender, text) {
  const chatBox = document.getElementById("chat-box");
  const messageElement = document.createElement("p");
  const msgId = "msg-" + Date.now(); // ID único para cada mensaje
  messageElement.id = msgId;
  messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
  chatBox.appendChild(messageElement);
  chatBox.scrollTop = chatBox.scrollHeight; // Scroll automático
  return msgId; // devolver el ID para actualizarlo después
}

// Actualizar un mensaje existente (ej. reemplazar "Escribiendo...")
function updateMessage(msgId, newText) {
  const messageElement = document.getElementById(msgId);
  if (messageElement) {
    messageElement.innerHTML = `<strong>Chatbot:</strong> ${newText}`;
  }
}

// Limpiar chat
function clearChat() {
  document.getElementById("chat-box").innerHTML = "";
}
