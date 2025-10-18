import requests
from wiki_api import WikiAPI
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os, json, time

# --- Flask App ---
app = Flask(__name__)

# --- Conexión global con la Wiki de la empresa ---
wiki = WikiAPI(
    base_url="https://objetivos.eldoradosrl.ar/wiki",
    username="Userapi",
    password="pr0y3ct0llm"
)

RAG_INDEX_PATH = "data/ingested/index.json"

# --- Cargar índice si existe ---
if os.path.exists(RAG_INDEX_PATH):
    with open(RAG_INDEX_PATH, "r", encoding="utf-8") as f:
        INDEX = json.load(f)
else:
    INDEX = []


# --- Función de respaldo: búsqueda textual simple ---
def retrieve_docs(query, k=3):
    """Búsqueda básica por coincidencia de texto (solo respaldo)."""
    results = []
    q = query.lower()
    for doc in INDEX:
        text = doc.get("text", "").lower()
        score = 0
        if q in text:
            score = 1
        else:
            common = sum(1 for w in q.split() if w in text)
            score = common
        if score > 0:
            results.append((score, doc))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:k]]


# --- Página principal ---
@app.route("/")
def index():
    return render_template("chat.html")


# --- CHAT PRINCIPAL (PDFs + Wiki + RAG) ---
@app.route("/api/chat", methods=["POST"])
def chat_api():
    from retriever import search_similar_chunks  # Import dinámico

    payload = request.json
    user_msg = payload.get("message", "")
    start = time.time()

    # === 1️⃣ Recuperar documentos locales (PDFs) con RAG ===
    try:
        chunks = search_similar_chunks(user_msg, top_k=5)
        if not chunks:
            # Fallback a búsqueda simple si no hay embeddings
            docs = retrieve_docs(user_msg, k=3)
            chunks = [d.get("text", "") for d in docs]
            fuentes_pdf = [d.get("file", "Desconocido") for d in docs]
        else:
            fuentes_pdf = ["RAG_index.json"]
        context_pdfs = "\n\n".join(chunks)
    except Exception as e:
        context_pdfs = f"[Error al buscar en índice semántico: {e}]"
        fuentes_pdf = []

    # === 2️⃣ Recuperar páginas de la Wiki ===
    wiki_context = ""
    fuentes_wiki = []
    try:
        wiki_results = wiki.search_pages(user_msg, 3)
        pages = wiki_results.get("query", {}).get("search", [])
        for p in pages:
            snippet = p.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            wiki_context += f"{p.get('title')}: {snippet}\n\n"
            fuentes_wiki.append(p.get("title"))
    except Exception as e:
        wiki_context = f"[Error al acceder a la Wiki: {e}]"

    # === 3️⃣ Combinar contexto total (limitado para evitar overflow) ===
    combined_context = (
        f"Documentos locales:\n{context_pdfs[:3000]}\n\n"
        f"Contenido de la Wiki:\n{wiki_context[:2000]}"
    )

    # === 4️⃣ Enviar al modelo en LM Studio ===
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "Meta-Llama-3-8B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sos un asistente técnico especializado en el sistema de gestión de calidad "
                    "de El Dorado SRL. Usá tanto los documentos PDF como la Wiki "
                    "para responder con precisión, citando la fuente si es posible."
                ),
            },
            {
                "role": "user",
                "content": f"Contexto:\n{combined_context}\n\nPregunta:\n{user_msg}",
            },
        ],
        "temperature": 0.4,
        "max_tokens": 512
    }

    try:
        r = requests.post(
            "http://192.168.68.50:1234/v1/chat/completions",
            headers=headers, json=data, timeout=60
        )
        if r.status_code == 200:
            llama_reply = r.json()["choices"][0]["message"]["content"]
        else:
            llama_reply = f"[Error {r.status_code}] {r.text}"
    except Exception as e:
        llama_reply = f"[Error al conectar con LM Studio: {e}]"

    latency = time.time() - start

    # === 5️⃣ Devolver respuesta con fuentes ===
    return jsonify({
        "response": llama_reply,
        "sources": {
            "pdfs": fuentes_pdf,
            "wiki": fuentes_wiki
        },
        "latency": round(latency, 2)
    })


# --- CONSULTAS DIRECTAS A LA WIKI ---
@app.route("/api/wiki", methods=["POST"])
def wiki_search():
    data = request.json
    query = data.get("query", "")
    limit = int(data.get("limit", 5))

    try:
        results = wiki.search_pages(query, limit)
        pages = results.get("query", {}).get("search", [])
        formatted = [
            {"title": p["title"], "snippet": p["snippet"]}
            for p in pages
        ]
        return jsonify({"results": formatted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- INDEXAR PDFs ---
@app.route("/api/index", methods=["POST"])
def api_index():
    from ingest_pdfs import build_index
    build_index()
    return jsonify({"msg": "Índice actualizado correctamente."})


# --- GENERAR EMBEDDINGS (RAG) ---
@app.route("/api/embed", methods=["POST"])
def api_embed():
    from retriever import build_rag_index
    build_rag_index()
    return jsonify({"msg": "✅ Embeddings generados correctamente."})


# --- BORRAR ARCHIVOS INDEXADOS ---
@app.route("/api/clear", methods=["POST"])
def api_clear():
    folder = "data/ingested"
    count = 0
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                count += 1
    return jsonify({"msg": f"🗑️ {count} archivos eliminados de la colección."})


# --- EXPORTAR ÍNDICE ---
@app.route("/api/export", methods=["GET"])
def export_index():
    index_path = "data/ingested/index.json"
    if not os.path.exists(index_path):
        return jsonify({"error": "No existe el índice para exportar."}), 404
    return send_from_directory(
        directory="data/ingested",
        path="index.json",
        as_attachment=True
    )


# --- IMPORTAR ÍNDICE ---
@app.route("/api/import", methods=["POST"])
def import_index():
    upload_folder = "data/ingested"
    os.makedirs(upload_folder, exist_ok=True)

    if "file" not in request.files:
        return jsonify({"error": "No se encontró archivo para importar."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".json"):
        return jsonify({"error": "Solo se permiten archivos .json."}), 400

    save_path = os.path.join(upload_folder, "index.json")
    file.save(save_path)
    print(f"✅ Índice importado en: {save_path}")
    return jsonify({"message": "✅ Índice importado correctamente."})


# --- SUBIR ARCHIVO PDF ---
@app.route("/upload", methods=["POST"])
def upload_file():
    upload_folder = "data/pdfs"
    os.makedirs(upload_folder, exist_ok=True)

    if "file" not in request.files:
        print("⚠️ No se encontró archivo en la solicitud.")
        return jsonify({"error": "No se encontró el archivo."}), 400

    file = request.files["file"]
    if file.filename == "":
        print("⚠️ Nombre de archivo vacío.")
        return jsonify({"error": "Nombre de archivo vacío."}), 400

    if not file.filename.lower().endswith(".pdf"):
        print("⚠️ Archivo no es PDF.")
        return jsonify({"error": "Solo se permiten archivos PDF."}), 400

    save_path = os.path.join(upload_folder, secure_filename(file.filename))
    file.save(save_path)
    print(f"✅ Archivo guardado en: {save_path}")
    return jsonify({"message": f"✅ Archivo '{file.filename}' subido correctamente."})


# --- EJECUCIÓN DEL SERVIDOR ---
if __name__ == "__main__":
    static_img_path = os.path.join(app.root_path, "static", "img")
    if os.path.exists(static_img_path):
        print("📁 Contenido de static/img:", os.listdir(static_img_path))
    else:
        print("❌ La carpeta static/img no existe.")
    app.run(host="0.0.0.0", port=5000, debug=True)
