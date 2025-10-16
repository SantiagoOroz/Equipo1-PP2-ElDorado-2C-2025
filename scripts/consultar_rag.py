import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pathlib import Path

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN (leída desde variables de entorno) ---
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/processed/chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EXTRACT_LENGTH = int(os.getenv("EXTRACT_LENGTH", 300))
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH") # Es obligatorio definirlo en .env

# Configuración del modelo Llama local
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", 0))
N_BATCH = int(os.getenv("N_BATCH", 1024))
N_THREADS = int(os.getenv("N_THREADS", 12))
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", 4096))


# --- PLANTILLA DEL PROMPT RAG ---
prompt_template = """<|start_header_id|>system<|end_header_id|>
Eres un asistente útil y experto. Tu tarea es utilizar únicamente los siguientes fragmentos de contexto para responder la pregunta del usuario. 
Si no encuentras la respuesta en el contexto, simplemente di que no tienes suficiente información. 
Cita la fuente y el número de página de donde proviene la información.

CONTEXTO:
{context}

<|eot_id|><|start_header_id|>user<|end_header_id|>

PREGUNTA: {question}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>
RESPUESTA CON CITA (Fuente y Página):
"""
RAG_PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])


# --- FUNCIÓN PRINCIPAL DE CONSULTA ---
def consultar(pregunta: str, qa_chain: RetrievalQA):
    """
    Ejecuta la consulta RAG con la pregunta dada y muestra los resultados.
    """
    print(f"\n-> Preguntando a Llama con RAG: '{pregunta}'")
    resultado = qa_chain.invoke({"query": pregunta})
    
    # Formatear la salida
    respuesta = resultado['result']
    fuentes = resultado['source_documents']
    
    print("\n--- RESPUESTA GENERADA POR LLAMA ---")
    print(respuesta)
    
    print("\n--- FUENTES RECUPERADAS (Para verificación) ---")
    for i, doc in enumerate(fuentes):
        source_path_full = doc.metadata.get('source', 'Desconocida')
        page = doc.metadata.get('page', 'N/A')
        source_name = Path(source_path_full).name
        
        print(f"[{i+1}] Fuente: {source_name}, Página: {page}")
        print(f"    Extracto (Primeros {EXTRACT_LENGTH} chars): {doc.page_content[:EXTRACT_LENGTH].strip()}...")
        print("-" * 40)
    return ""


def inicializar_rag_chain():
    """
    Inicializa todos los componentes de la cadena RAG (Embeddings, Chroma, Llama)
    para ser reutilizados en el bucle interactivo.
    """
    # Verificación de la ruta del modelo LLAMA
    if not LLAMA_MODEL_PATH or not os.path.exists(LLAMA_MODEL_PATH):
        print(f"Error: La variable 'LLAMA_MODEL_PATH' no está configurada en el archivo .env o la ruta es inválida.")
        print(f"Ruta configurada: {LLAMA_MODEL_PATH}")
        print("Por favor, verifica el archivo .env.")
        return None

    # Verificación del directorio de ChromaDB
    if not os.path.exists(CHROMA_DIR):
        print(f"Error: No se encontró la Base de Datos Vectorial en '{CHROMA_DIR}'.")
        print("Ejecuta primero 'rag_indexer.py' para crearla.")
        return None

    try:
        # 1. Cargar el modelo de embeddings
        embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # 2. Cargar la Base de Datos Vectorial Persistente
        print(f"-> Cargando Base de Datos Vectorial desde: {CHROMA_DIR}")
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        
        # 3. Inicializar el LLM (LlamaCpp)
        print("-> Inicializando el modelo LLAMA...")
        llm = LlamaCpp(
            model_path=LLAMA_MODEL_PATH,
            temperature=0.1,
            max_tokens=512, 
            n_ctx=CONTEXT_WINDOW,
            n_gpu_layers=N_GPU_LAYERS,
            n_batch=N_BATCH,
            n_threads=N_THREADS, 
            verbose=False,
        )

        # 4. Crear la Cadena RAG (RetrievalQA)
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


if __name__ == "__main__":
    qa_chain = inicializar_rag_chain()
    
    if qa_chain is None:
        exit()

    print("\n--- INICIO DE CONSULTA INTERACTIVA RAG ---")
    print("Escribe tu pregunta (o 'salir' para finalizar).")

    while True:
        try:
            pregunta_usuario = input("\nTu pregunta ❓: ").strip()
            
            if pregunta_usuario.lower() in ['salir', 'exit', 'quit']:
                print("Saliendo del modo de consulta. ¡Adiós!")
                break
            
            if not pregunta_usuario:
                continue
                
            consultar(pregunta_usuario, qa_chain)

        except KeyboardInterrupt:
            print("\nSaliendo del modo de consulta por interrupción de teclado. ¡Adiós!")
            break
        except Exception as e:
            print(f"Ocurrió un error inesperado en el bucle: {e}")
            break