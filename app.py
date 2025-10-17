# app.py
from flask import Flask, render_template, request, jsonify
import sys
import threading # NUEVO: Importamos la librería para hilos
from pathlib import Path

# Añadir la carpeta 'scripts' al path para poder importar rag_core
sys.path.append(str(Path(__file__).resolve().parent / "scripts"))
from rag_core import inicializar_rag_chain, consultar_rag

# --- INICIALIZACIÓN DE LA APLICACIÓN FLASK ---
app = Flask(__name__)

# --- ESTADO GLOBAL DE LA APLICACIÓN (NUEVO) ---
# Usaremos un diccionario para mantener el estado del modelo.
# Estados posibles: "cargando", "listo", "error"
app_state = {
    "status": "cargando",
    "chain": None
}

# Almacenaremos el historial en memoria
conversation_history = []


# --- FUNCIÓN PARA CARGAR EL MODELO EN SEGUNDO PLANO (NUEVO) ---
def load_model_in_background():
    """
    Esta función se ejecuta en un hilo separado para no bloquear el servidor.
    """
    print("--- INICIANDO CARGA DEL MODELO RAG EN SEGUNDO PLANO ---")
    print("Este proceso puede tardar varios minutos...")
    
    chain = inicializar_rag_chain()
    
    if chain:
        app_state["status"] = "listo"
        app_state["chain"] = chain
        print("--- ¡Modelo cargado! El servidor está listo para recibir consultas. ---")
    else:
        app_state["status"] = "error"
        print("!!! ERROR CRÍTICO: No se pudo inicializar la cadena RAG. !!!")


# --- DEFINICIÓN DE RUTAS ---

@app.route('/')
def index():
    """
    Renderiza la página principal. Muestra una página de carga si el modelo
    aún no está listo.
    """
    # MODIFICADO: Comprueba el estado antes de mostrar la página
    if app_state["status"] == "cargando":
        return render_template('loading.html') # Página de carga
    elif app_state["status"] == "listo":
        return render_template('index.html', history=conversation_history)
    else: # "error"
        # Opcional: Podrías crear una página de error.html
        return "<h1>Error al cargar el modelo. Por favor, revisa la consola del servidor.</h1>"


@app.route('/ask', methods=['POST'])
def ask():
    """
    Recibe preguntas del usuario, las procesa con RAG y devuelve una respuesta.
    """
    # MODIFICADO: Verifica que el modelo esté listo
    if app_state["status"] != "listo":
        return jsonify({
            "error": "El modelo no está disponible o sigue cargando. Inténtalo de nuevo en unos momentos."
        }), 503 # Service Unavailable

    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No se recibió ninguna pregunta."}), 400

    conversation_history.append({"type": "user", "content": user_question})

    print(f"-> Recibida pregunta: '{user_question}'")
    # Usa la cadena RAG guardada en app_state
    result = consultar_rag(user_question, app_state["chain"])
    
    conversation_history.append({"type": "assistant", "content": result})
    
    print(f"-> Enviando respuesta...")
    return jsonify(result)

# --- EJECUCIÓN DEL SERVIDOR ---

# NUEVO: Iniciar el hilo de carga del modelo
loader_thread = threading.Thread(target=load_model_in_background)
loader_thread.start()

if __name__ == '__main__':
    # Ahora que no carga el modelo aquí, debug=False es más directo.
    app.run(host='0.0.0.0', port=5000, debug=False)