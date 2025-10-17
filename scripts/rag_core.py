# scripts/rag_core.py
import os
import gc
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN (leída desde variables de entorno) ---
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/processed/chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EXTRACT_LENGTH = int(os.getenv("EXTRACT_LENGTH", 300))
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH")

# Configuración del modelo Llama
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", 0))
N_BATCH = int(os.getenv("N_BATCH", 1024))
N_THREADS = int(os.getenv("N_THREADS", 12))
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", 4096))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

# --- PLANTILLA DEL PROMPT RAG ---
prompt_template = """<|start_header_id|>system<|end_header_id|>
Sos un asistente especializado y experto en todo lo relacionado con el hormigón. Tu función es basarte únicamente en los documentos proporcionados para asistir al personal de la empresa El Dorado S.R.L., ubicada en Río Grande, Tierra del Fuego, Argentina.

Debés:
Brindar respuestas claras, explicativas y comprensibles para un público con niveles educativos diversos.
Mantener siempre un tono formal, en español rioplatense (el que se usa en Argentina).
Respaldar tus afirmaciones con citas explícitas.
Si la consulta no está contemplada en los documentos, tenés que informarle al usuario que no contás con esa información y sugerirle que reformule su consulta.

CONTEXTO:
{context}

<|eot_id|><|start_header_id|>user<|end_header_id|>

PREGUNTA: {question}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RESPUESTA:
"""
RAG_PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

def inicializar_llm():
    """Inicializa y devuelve únicamente el modelo LLM (LlamaCpp)."""
    if not LLAMA_MODEL_PATH or not os.path.exists(LLAMA_MODEL_PATH):
        print(f"Error: La variable 'LLAMA_MODEL_PATH' es inválida: {LLAMA_MODEL_PATH}")
        return None
    try:
        llm = LlamaCpp(
            model_path=LLAMA_MODEL_PATH,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            n_ctx=CONTEXT_WINDOW,
            n_gpu_layers=N_GPU_LAYERS,
            n_batch=N_BATCH,
            n_threads=N_THREADS,
            verbose=False,
        )
        return llm
    except Exception as e:
        print(f"Ocurrió un error durante la inicialización del LLM: {e}")
        return None

def consultar_rag(pregunta: str, llm: LlamaCpp):
    """
    Ejecuta la consulta RAG conectándose a la BD bajo demanda.
    """
    if not pregunta:
        return {"answer": "Por favor, realiza una pregunta.", "sources": []}
    
    if not os.path.exists(CHROMA_DIR) or not any(Path(CHROMA_DIR).iterdir()):
        return {"answer": "La base de datos vectorial no existe o está vacía. Por favor, indexa documentos primero.", "sources": []}

    # --- Conexión a ChromaDB bajo demanda ---
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    
    # Crear la cadena QA justo para esta consulta
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 2}),
        chain_type_kwargs={"prompt": RAG_PROMPT},
        return_source_documents=True
    )

    resultado = qa_chain.invoke({"query": pregunta})
    
    # --- Formatear las fuentes ---
    fuentes_formateadas = []
    for doc in resultado.get('source_documents', []):
        source_path_full = doc.metadata.get('source', 'Desconocida')
        page = doc.metadata.get('page', 'N/A')
        source_name = Path(source_path_full).name
        extracto = doc.page_content[:EXTRACT_LENGTH].strip()
        fuentes_formateadas.append({
            "name": source_name,
            "page": page,
            "extract": f"{extracto}..."
        })
        
    respuesta_final = {
        "answer": resultado.get('result', 'No se pudo generar una respuesta.'),
        "sources": fuentes_formateadas
    }
    # Liberar recursos
    del qa_chain
    del db
    gc.collect()
    return respuesta_final