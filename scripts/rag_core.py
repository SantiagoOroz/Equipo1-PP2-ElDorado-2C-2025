# scripts/rag_core.py
import os
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


def inicializar_rag_chain():
    """Inicializa todos los componentes de la cadena RAG."""
    if not LLAMA_MODEL_PATH or not os.path.exists(LLAMA_MODEL_PATH):
        print(f"Error: La variable 'LLAMA_MODEL_PATH' es inválida: {LLAMA_MODEL_PATH}")
        return None
    if not os.path.exists(CHROMA_DIR):
        print(f"Error: No se encontró la BD Vectorial en '{CHROMA_DIR}'.")
        return None

    try:
        embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        
        llm = LlamaCpp(
            model_path=LLAMA_MODEL_PATH,
            temperature=0.1,
            max_tokens=MAX_TOKENS,
            n_ctx=CONTEXT_WINDOW,
            n_gpu_layers=N_GPU_LAYERS,
            n_batch=N_BATCH,
            n_threads=N_THREADS,
            verbose=False,
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={"k": 2}),
            chain_type_kwargs={"prompt": RAG_PROMPT},
            return_source_documents=True
        )
        return qa_chain
    except Exception as e:
        print(f"Ocurrió un error durante la inicialización RAG: {e}")
        return None


def consultar_rag(pregunta: str, qa_chain: RetrievalQA):
    """
    Ejecuta la consulta RAG y devuelve un diccionario con la respuesta y las fuentes.
    """
    if not pregunta:
        return {"answer": "Por favor, realiza una pregunta.", "sources": []}

    resultado = qa_chain.invoke({"query": pregunta})
    
    # Formatear las fuentes para devolverlas
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
        
    return {
        "answer": resultado.get('result', 'No se pudo generar una respuesta.'),
        "sources": fuentes_formateadas
    }