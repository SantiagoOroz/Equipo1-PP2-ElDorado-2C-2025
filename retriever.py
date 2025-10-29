# retriever.py
from sentence_transformers import SentenceTransformer, util
import numpy as np
import json, os

MODEL_NAME = "all-MiniLM-L6-v2"
CHUNKS_FILE = "data/ingested/chunks.json"
EMB_FILE = "data/ingested/embeddings.npy"

model = SentenceTransformer(MODEL_NAME)

def build_rag_index():
    """
    Crea embeddings de los fragmentos de texto del índice existente (sin FAISS).
    """
    index_path = "data/ingested/index.json"
    if not os.path.exists(index_path):
        print("⚠️ No existe index.json. Ejecutá primero la indexación de PDFs.")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    texts = []
    for doc in docs:
        text = doc.get("text", "").strip()
        if not text:
            continue
        # Dividir texto largo en fragmentos de 500 caracteres
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        texts.extend(chunks)

    print(f"🔍 Generando embeddings para {len(texts)} fragmentos...")
    embeddings = model.encode(texts, convert_to_numpy=True)

    os.makedirs("data/ingested", exist_ok=True)
    np.save(EMB_FILE, embeddings)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

    print("✅ Embeddings generados y guardados correctamente.")


def search_similar_chunks(query, top_k=5):
    """
    Busca los fragmentos más similares al texto de consulta.
    """
    if not os.path.exists(EMB_FILE):
        print("⚠️ No existen embeddings. Ejecutá build_rag_index() primero.")
        return []

    embeddings = np.load(EMB_FILE)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        texts = json.load(f)

    q_emb = model.encode([query], convert_to_numpy=True)
    scores = util.cos_sim(q_emb, embeddings)[0].cpu().numpy()
    best_idx = np.argsort(scores)[::-1][:top_k]
    results = [texts[i] for i in best_idx]
    return results
