# app.py
from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path

# Añadir la carpeta 'scripts' al path para poder importar rag_core
sys.path.append(str(Path(__file__).resolve().parent / "scripts"))

# Ahora podemos importar desde el módulo
from rag_core import inicializar_rag_chain, consultar_rag

# --- INICIALIZACIÓN DE LA APLICACIÓN FLASK ---
app = Flask(__name__)

# --- CARGA DEL MODELO RAG (se hace una sola vez al iniciar) ---
print("--- INICIANDO SERVIDOR Y CARGANDO MODELO RAG ---")
print("Este proceso puede tardar varios minutos. Por favor, espere...")

qa_chain = inicializar_rag_chain()

if qa_chain is None:
    print("!!! ERROR CRÍTICO: No se pudo inicializar la cadena RAG. El servidor no funcionará correctamente. !!!")
else:
    print("--- ¡Modelo cargado! Servidor listo para recibir consultas. ---")

# Almacenaremos el historial en memoria
conversation_history = []

# --- DEFINICIÓN DE RUTAS ---

@app.route('/')
def index():
    """Renderiza la página principal del chat."""
    # Pasamos el historial para que se muestre al recargar
    return render_template('index.html', history=conversation_history)

@app.route('/ask', methods=['POST'])
def ask():
    """Recibe preguntas del usuario, las procesa con RAG y devuelve una respuesta."""
    if qa_chain is None:
        return jsonify({
            "error": "El modelo no está disponible. Revisa la consola del servidor para más detalles."
        }), 500

    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No se recibió ninguna pregunta."}), 400

    # Añadimos la pregunta del usuario al historial
    conversation_history.append({"type": "user", "content": user_question})

    # Obtenemos la respuesta del modelo
    print(f"-> Recibida pregunta: '{user_question}'")
    result = consultar_rag(user_question, qa_chain)
    
    # Añadimos la respuesta del asistente al historial
    conversation_history.append({"type": "assistant", "content": result})
    
    print(f"-> Enviando respuesta...")
    return jsonify(result)

# --- EJECUCIÓN DEL SERVIDOR ---
if __name__ == '__main__':
    # Usar debug=False en producción
    app.run(host='0.0.0.0', port=5000, debug=True)