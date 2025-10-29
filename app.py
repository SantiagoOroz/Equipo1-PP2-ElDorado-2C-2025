import requests
import os
import json
import time
import shutil
import zipfile
import io
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv

# --- Importar módulos RAG y Wiki ---
from wiki_api import WikiAPI
from indexing import create_and_persist_index 
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# --- Cargar variables de entorno ---
load_dotenv()

# --- CONFIGURACIÓN (leída desde .env) ---
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

WIKI_BASE_URL = os.getenv("WIKI_BASE_URL")
WIKI_USERNAME = os.getenv("WIKI_USERNAME")
WIKI_PASSWORD = os.getenv("WIKI_PASSWORD")

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Meta-Llama-3-8B-Instruct")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
PDF_TOP_K = int(os.getenv("PDF_TOP_K", 3))
WIKI_TOP_K = int(os.getenv("WIKI_TOP_K", 3))
EXTRACT_LENGTH = int(os.getenv("EXTRACT_LENGTH", 300))

# --- Inicialización de Flask ---
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}) 

# # --- Inicialización y Login de la Wiki ---
print(f"Conectando a la Wiki en: {WIKI_BASE_URL}...")
wiki = WikiAPI(
    base_url=WIKI_BASE_URL,
    username=WIKI_USERNAME,
    password=WIKI_PASSWORD
)

# Forzar el login al iniciar la app para verificar credenciales
try:
    wiki.login() 
except Exception as e:
    print("="*50)
    print(f"ATENCIÓN: No se pudo conectar a la Wiki.")
    print(f"Error: {e}")
    print("Verifica WIKI_BASE_URL, WIKI_USERNAME, y WIKI_PASSWORD en tu archivo .env")
    print("La app continuará, pero la Wiki NO funcionará.")
    print("="*50)
# # --- Lista de Stopwords para la Wiki ---
SPANISH_STOPWORDS = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra", 
    "cual", "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "ella", 
    "ellas", "ellos", "en", "entre", "era", "es", "esa", "esas", "ese", "eso", "esos", 
    "esta", "estas", "este", "esto", "estos", "estoy", "etc", "ha", "hasta", "hay", 
    "la", "las", "le", "les", "lo", "los", "mas", "me", "mi", "mis", "muy", "no", "nos", 
    "o", "os", "otra", "otras", "otro", "otros", "para", "pero", "por", "porque", "que", 
    "se", "sea", "sean", "seas", "ser", "si", "sin", "sobre", "sois", "solo", "somos", 
    "soy", "su", "sus", "te", "tu", "tus", "un", "una", "uno", "unos", "y", "ya", "yo"
]
QUERY_STOPWORDS = [
    "consulta", "wiki", "dame", "decime", "dime", "pregunta", "explicame", "que", "es",
    "info", "informacion", "sobre", "acerca", "de", "los", "las", "el", "la", "cuales",
    "cuales", "son", "tenes", "tienes", "podes", "puedes"
]
STOPWORD_SET = set(SPANISH_STOPWORDS + QUERY_STOPWORDS)

def get_wiki_keywords_fast(query: str) -> str:
    """
    Limpia la consulta del usuario de stopwords para mejorar la búsqueda en la Wiki.
    Es una función local y rápida, no usa el LLM.
    """
    clean_query = re.sub(r'[^\w\s]', '', query.lower())
    keywords = [word for word in clean_query.split() if word not in STOPWORD_SET]
    
    if not keywords:
        print(f"No se pudieron extraer keywords, usando consulta original: '{query}'")
        return query
        
    keyword_string = " ".join(keywords)
    print(f"Keywords filtrados para la Wiki: '{keyword_string}'")
    return keyword_string

def get_rag_context(query: str, top_k: int):
    """
    Busca en ChromaDB y devuelve el contexto y las fuentes.
    """
    if not os.path.exists(CHROMA_DIR) or not any(Path(CHROMA_DIR).iterdir()):
        print("Advertencia: ChromaDB no existe o está vacía.")
        return "", []
    try:
        embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        retriever = db.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        context_chunks = []
        fuentes_pdf = []
        for doc in docs:
            context_chunks.append(doc.page_content)
            source_name = doc.metadata.get('source', 'Desconocida')
            page = doc.metadata.get('page', 'N/A')
            extracto = doc.page_content[:EXTRACT_LENGTH].strip()
            fuentes_pdf.append({
                "name": source_name,
                "page": page,
                "extract": f"{extracto}..."
            })
        context_pdfs = "\n\n".join(context_chunks)
        return context_pdfs, fuentes_pdf
    except Exception as e:
        print(f"Error al consultar ChromaDB: {e}")
        return f"[Error al buscar en índice: {e}]", []


@app.route("/")
def index():
    return render_template("chat.html") 


@app.route("/api/chat", methods=["POST"])
def chat_api():
    payload = request.json
    user_msg = payload.get("message", "")
    if not user_msg:
        return jsonify({"error": "Mensaje vacío"}), 400

    start = time.time()

    # === 1️⃣ Recuperar documentos locales (PDFs) con RAG y fuentes ===
    context_pdfs, fuentes_pdf = get_rag_context(user_msg, top_k=PDF_TOP_K)

    # === 2️⃣ Recuperar páginas de la Wiki (con filtro rápido) ===
    wiki_context = ""
    fuentes_wiki = []
    try:
        # Paso A: Obtener keywords con el filtro rápido (SIN LLM)
        wiki_search_terms = get_wiki_keywords_fast(user_msg)
        
        # Paso B: Buscar artículos con esos keywords
        print(f"Buscando en Wiki con keywords: '{wiki_search_terms}'")
        wiki_results = wiki.search_pages(wiki_search_terms, WIKI_TOP_K)
        pages = wiki_results.get("query", {}).get("search", [])
        
        if not pages:
            print("No se encontraron artículos de Wiki con esos keywords.")
        
        # Paso C: Por cada artículo, obtener su RESUMEN
        for p in pages:
            title = p.get('title')
            if not title:
                continue

            print(f"Obteniendo resumen de Wiki para: {title}")
            summary_data = wiki.get_page_summary(title)
            page_id = list(summary_data.get("query", {}).get("pages", {}).keys())[0]
            
            if page_id and page_id != "-1":
                summary = summary_data["query"]["pages"][page_id].get("extract", "")
                if summary:
                    wiki_context += f"Título (Wiki): {title}\nResumen: {summary}\n\n"
                    fuentes_wiki.append({
                        "name": title,
                        "page": "Wiki",
                        "extract": f"{summary[:EXTRACT_LENGTH]}..."
                    })
                else:
                    snippet = p.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                    if snippet:
                        wiki_context += f"Título (Wiki): {title}\nSnippet: {snippet}\n\n"
                        fuentes_wiki.append({
                            "name": title,
                            "page": "Wiki",
                            "extract": f"{snippet}..."
                        })
    except Exception as e:
        wiki_context = f"[Error al acceder a la Wiki: {e}]"
        print(f"Error de Wiki API: {e}")

    # === 3️⃣ Combinar contexto total ===
    combined_context = (
        f"Documentos locales:\n{context_pdfs}\n\n"
        f"Contenido de la Wiki:\n{wiki_context}"
    )

    # --- Prompt del Sistema Mejorado ---
    system_content = f"""
Sos un asistente técnico especializado y experto en hormigón para la empresa El Dorado S.R.L. en Río Grande, Tierra del Fuego.
Tu función es responder al usuario basándote ÚNICA Y EXCLUSIVAMENTE en el siguiente contexto.
El contexto incluye información de documentos PDF internos y de la Wiki de la empresa.

REGLAS ESTRICTAS:
1.  **NO SALUDES** ni uses frases introductorias como "¡Hola!", "Claro, aquí tienes", "Como asistente...", "Basado en el contexto que me diste...". Responde directamente a la pregunta.
2.  **BASATE SÓLO EN EL CONTEXTO.** Si la respuesta no está en el contexto, DEBES responder: "No cuento con esa información en mis documentos." No intentes adivinar ni uses conocimiento externo.
3.  Mantén un tono formal, en español rioplatense (argentino).
4.  Responde de forma clara y explicativa.

--- CONTEXTO PROPORCIONADO ---
{combined_context}
--- FIN DEL CONTEXTO ---
""".strip()

    # === 4️⃣ Enviar al modelo en LM Studio (¡UNA SOLA VEZ!) ===
    headers = {"Content-Type": "application/json"}
    data = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_content },
            {"role": "user", "content": user_msg },
        ],
        "temperature": 0.4,
    }

    try:
        r = requests.post(LM_STUDIO_URL, headers=headers, json=data, timeout=600)
        if r.status_code == 200:
            llama_reply = r.json()["choices"][0]["message"]["content"]
        else:
            llama_reply = f"[Error {r.status_code}] {r.text}"
    except Exception as e:
        llama_reply = f"[Error al conectar con LM Studio: {e}]"

    latency = time.time() - start

    # === 5️⃣ Devolver respuesta con fuentes DETALLADAS ===
    return jsonify({
        "reply": llama_reply,
        "response": llama_reply, 
        "sources": {
            "pdfs": fuentes_pdf, 
            "wiki": fuentes_wiki
        },
        "latency": round(latency, 2)
    })


# --- Rutas de Administración ---

@app.route("/api/index", methods=["POST"])
def api_index():
    try:
        result = create_and_persist_index()
        if result.get("ok"):
            return jsonify({"msg": f"✅ Índice actualizado. {result['docs']} documentos procesados."})
        else:
            return jsonify({"msg": f"Error en la indexación: {result.get('error')}"}), 500
    except Exception as e:
        return jsonify({"msg": f"Error crítico al indexar: {str(e)}"}), 500

@app.route("/api/clear", methods=["POST"])
def api_clear():
    try:
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            os.makedirs(CHROMA_DIR, exist_ok=True)
        return jsonify({"msg": f"🗑️ Índice de ChromaDB eliminado."})
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route("/api/export", methods=["GET"])
def export_index():
    if not any(Path(CHROMA_DIR).iterdir()):
        return jsonify({"error": "No hay un índice para exportar."}), 404
    
    mem_file = io.BytesIO()
    with zipfile.ZipFile(mem_file, "w", zipfile.ZIP_DEFLATED) as zf:
        base_dir = Path(CHROMA_DIR)
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                full_path = Path(root) / f
                arc_name = str(full_path.relative_to(base_dir))
                zf.write(full_path, arcname=arc_name)
    mem_file.seek(0)
    
    return send_file(
        mem_file, 
        mimetype="application/zip", 
        as_attachment=True, 
        download_name="chroma_index.zip"
    )

@app.route("/api/import", methods=["POST"])
def import_index():
    if "file" not in request.files:
        return jsonify({"error": "No se encontró archivo."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".zip"):
        return jsonify({"error": "Solo se permiten archivos .zip."}), 400

    try:
        if os.path.isdir(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
        os.makedirs(CHROMA_DIR, exist_ok=True)
        
        with zipfile.ZipFile(file, "r") as z:
            z.extractall(CHROMA_DIR)
        
        return jsonify({"message": "✅ Índice importado correctamente."})
    except Exception as e:
        return jsonify({"error": f"Error al extraer el ZIP: {e}"}), 500

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No se encontró el archivo."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío."}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Solo se permiten archivos PDF."}), 400

    save_path = os.path.join(UPLOAD_DIR, secure_filename(file.filename))
    file.save(save_path)
    return jsonify({"message": f"✅ Archivo '{file.filename}' subido a /data/uploads."})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# --- EJECUCIÓN DEL SERVIDOR ---
if __name__ == "__main__":
    print(f"🚀 Iniciando servidor Flask en http://localhost:5000")
    print(f"Buscando índice RAG en: {CHROMA_DIR}")
    print(f"Conectando a LM Studio en: {LM_STUDIO_URL}")
    app.run(host="0.0.0.0", port=5000, debug=False)