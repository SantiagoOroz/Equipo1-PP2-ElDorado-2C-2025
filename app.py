# app.py
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import sys
import threading
import os
import shutil
import zipfile
import io
import time
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Añadir la carpeta 'scripts' al path
sys.path.append(str(Path(__file__).resolve().parent / "scripts"))
from rag_core import inicializar_rag_chain, consultar_rag
from indexing import create_and_persist_index # NUEVO: Importamos la función de indexación

# --- CONFIGURACIÓN Y VARIABLES GLOBALES ---
PDF_DIR = Path(os.getenv("PDF_DIR", "data/raw/Antecedentes PDF"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "data/processed/chroma_db"))

# Crear directorios si no existen
PDF_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "un-secreto-muy-secreto")

app_state = {
    "status": "cargando", # "cargando", "listo", "error", "sin_indice"
    "chain": None
}

conversation_history = []

# --- LÓGICA DE CARGA DEL MODELO Y ESTADO ---
def load_model_in_background():
    """Carga o recarga la cadena RAG en un hilo separado."""
    print("--- INICIANDO CARGA DEL MODELO RAG EN SEGUNDO PLANO ---")
    
    # Comprobar si existe el índice antes de cargar
    if not any(Path(CHROMA_DIR).iterdir()):
        app_state["status"] = "sin_indice"
        print("!!! ADVERTENCIA: La base de datos vectorial está vacía. Es necesario indexar documentos. !!!")
        return

    chain = inicializar_rag_chain()
    if chain:
        app_state["status"] = "listo"
        app_state["chain"] = chain
        print("--- ¡Modelo cargado! El servidor está listo para recibir consultas. ---")
    else:
        app_state["status"] = "error"
        print("!!! ERROR CRÍTICO: No se pudo inicializar la cadena RAG. !!!")

def reload_rag_chain():
    """Función para disparar la recarga del modelo en un nuevo hilo."""
    app_state["status"] = "cargando"
    app_state["chain"] = None
    loader_thread = threading.Thread(target=load_model_in_background)
    loader_thread.start()

# --- RUTAS DE LA INTERFAZ DE USUARIO (UI) ---
@app.route('/')
def index():
    """Renderiza la página principal con el chat y el panel de control."""
    if app_state["status"] == "cargando":
        return render_template('loading.html')
    
    # Listar PDFs para mostrar en el panel
    local_pdfs = sorted([p.name for p in PDF_DIR.glob("*.pdf")])
    uploaded_pdfs = sorted([p.name for p in UPLOAD_DIR.glob("*.pdf")])
    
    return render_template(
        'index.html',
        history=conversation_history,
        local_pdfs=local_pdfs,
        uploaded_pdfs=uploaded_pdfs,
        app_status=app_state["status"] # Pasamos el estado a la plantilla
    )

# --- RUTAS DE LA API (PARA EL CHAT Y EL PANEL) ---
@app.route('/ask', methods=['POST'])
def ask():
    """Recibe preguntas del usuario, las procesa con RAG y devuelve una respuesta."""
    if app_state["status"] != "listo":
        error_messages = {
            "cargando": "El modelo sigue cargando. Inténtalo de nuevo en unos momentos.",
            "sin_indice": "No hay una base de conocimiento cargada. Por favor, indexa documentos primero.",
            "error": "El modelo no está disponible debido a un error."
        }
        return jsonify({"error": error_messages.get(app_state["status"], "Error desconocido.")}), 503

    user_question = request.json.get('question')
    if not user_question:
        return jsonify({"error": "No se recibió ninguna pregunta."}), 400

    conversation_history.append({"type": "user", "content": user_question})
    result = consultar_rag(user_question, app_state["chain"])
    conversation_history.append({"type": "assistant", "content": result})
    
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API para subir archivos PDF."""
    f = request.files.get("pdf_file")
    if not f or f.filename == "":
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for('index'))
    if not f.filename.lower().endswith(".pdf"):
        flash("Solo se permiten archivos PDF.", "error")
        return redirect(url_for('index'))
    
    dest = UPLOAD_DIR / f.filename
    f.save(dest)
    flash(f"Archivo '{f.filename}' subido correctamente.", "success")
    return redirect(url_for('index'))

@app.route('/api/index', methods=['POST'])
def api_index():
    """API para lanzar el proceso de indexación."""
    app_state["status"] = "cargando"

    # Liberar la conexión con la BD
    app_state["chain"] = None
    time.sleep(0.1) # Damos un instante para que el sistema libere el archivo
    
    # Borramos el índice viejo para evitar duplicados
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    result = create_and_persist_index()

    if result.get("ok"):
        flash(f"Indexación completada. Se procesaron {result['docs']} documentos en {result['chunks']} fragmentos.", "success")
        reload_rag_chain()
    else:
        flash(f"Error en la indexación: {result.get('error', 'Error desconocido')}", "error")
        app_state["status"] = "sin_indice"

    return redirect(url_for('index'))

@app.route('/api/wipe', methods=['POST'])
def api_wipe():
    """API para borrar la base de datos vectorial."""
    # Liberar la conexión con la BD
    app_state["chain"] = None
    time.sleep(0.1) # Damos un instante para que el sistema libere el archivo

    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        os.makedirs(CHROMA_DIR, exist_ok=True)

    app_state["status"] = "sin_indice"
    flash("La base de conocimiento ha sido eliminada.", "success")
    return redirect(url_for('index'))

@app.route('/api/export', methods=['POST'])
def api_export():
    """API para exportar el índice como un archivo ZIP."""
    if not any(Path(CHROMA_DIR).iterdir()):
        flash("No hay un índice para exportar.", "error")
        return redirect(url_for('index'))

    mem_file = io.BytesIO()
    with zipfile.ZipFile(mem_file, "w", zipfile.ZIP_DEFLATED) as zf:
        base_dir = Path(CHROMA_DIR)
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                full_path = Path(root) / f
                arc_name = str(full_path.relative_to(base_dir))
                zf.write(full_path, arcname=arc_name)
    mem_file.seek(0)
    
    return send_file(mem_file, mimetype="application/zip", as_attachment=True, download_name="chroma_index.zip")

@app.route('/api/import', methods=['POST'])
def api_import():
    """API para importar un índice desde un archivo ZIP."""
    file = request.files.get("zip_file")
    if not file or file.filename == "":
        flash("No se seleccionó ningún archivo ZIP.", "error")
        return redirect(url_for('index'))
    if not file.filename.lower().endswith(".zip"):
        flash("Debe ser un archivo .zip.", "error")
        return redirect(url_for('index'))
    
    # Liberar la conexión con la BD (creo que no es necesario pero por las dudas)
    app_state["chain"] = None
    time.sleep(0.1)
    # Borrar el índice actual
    if os.path.isdir(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    
    # Extraer el nuevo índice
    with zipfile.ZipFile(file, "r") as z:
        z.extractall(CHROMA_DIR)
    
    flash("Índice importado correctamente. Recargando modelo...", "success")
    reload_rag_chain()
    return redirect(url_for('index'))

# --- EJECUCIÓN DEL SERVIDOR ---
# Iniciar la carga inicial del modelo en un hilo
initial_loader_thread = threading.Thread(target=load_model_in_background)
initial_loader_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)