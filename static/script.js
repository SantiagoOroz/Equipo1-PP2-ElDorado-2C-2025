// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatContainer = document.getElementById('chat-container');
    const loadingIndicator = document.getElementById('loading-indicator');

    // Mover el scroll al final al cargar la página
    chatContainer.scrollTop = chatContainer.scrollHeight;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();

        if (!question) return;

        // 1. Mostrar la pregunta del usuario inmediatamente
        appendMessage('user', question);
        userInput.value = '';

        // 2. Mostrar el indicador de carga
        loadingIndicator.style.display = 'block';
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            // 3. Enviar la pregunta al backend
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.statusText}`);
            }

            const data = await response.json();
            
            // 4. Ocultar el indicador de carga y mostrar la respuesta del asistente
            loadingIndicator.style.display = 'none';
            appendMessage('assistant', data);

        } catch (error) {
            console.error('Error al contactar al servidor:', error);
            loadingIndicator.style.display = 'none';
            const errorData = { answer: `Lo siento, ocurrió un error al procesar tu solicitud: ${error.message}`, sources: [] };
            appendMessage('assistant', errorData);
        }
    });

    function appendMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'bubble';

        if (type === 'user') {
            bubbleDiv.textContent = content;
        } else {
            // El contenido es un objeto { answer, sources }
            const answerP = document.createElement('p');
            answerP.innerHTML = content.answer.replace(/\n/g, '<br>'); // Respeta saltos de línea
            bubbleDiv.appendChild(answerP);

            if (content.sources && content.sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = '<strong>Fuentes:</strong>';
                
                const ul = document.createElement('ul');
                content.sources.forEach(source => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${source.name} (Pág: ${source.page})</strong>
                                    <blockquote>${source.extract}</blockquote>`;
                    ul.appendChild(li);
                });
                sourcesDiv.appendChild(ul);
                bubbleDiv.appendChild(sourcesDiv);
            }
        }
        
        messageDiv.appendChild(bubbleDiv);
        chatContainer.appendChild(messageDiv);

        // Mover el scroll al final para ver el nuevo mensaje
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});