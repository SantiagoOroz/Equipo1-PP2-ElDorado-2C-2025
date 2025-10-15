# consultar_rag.py
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pathlib import Path # Importar Path para manejo limpio de rutas

# --- CONFIGURACIÓN ---
# Directorios y Nombres deben coincidir con rag_indexer.py
CHROMA_DIR = "data/processed/chroma_db"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EXTRACT_LENGTH = 300 # Cantidad de caracteres a mostrar del chunk recuperado

# Configuración del modelo Llama local
# RUTA a tu modelo Llama descargado (ej: Meta-Llama-3-8B-Instruct.Q4_K_M.gguf)
# AJUSTA ESTA RUTA A TU ARCHIVO .gguf
LLAMA_MODEL_PATH = r"C:\Users\capod\.lmstudio\models\lmstudio-community\Llama-3.2-1B-Instruct-GGUF\Llama-3.2-1B-Instruct-Q8_0.gguf"
N_GPU_LAYERS = 40       # Número de capas a descargar a la GPU (ajusta según tu hardware)
N_BATCH = 512           # Tamaño de lote
CONTEXT_WINDOW = 4096   # Ventana de contexto del modelo

# --- PLANTILLA DEL PROMPT RAG ---
prompt_template = """
Utiliza únicamente los siguientes fragmentos de contexto para responder la pregunta. 
Si no encuentras la respuesta en el contexto, simplemente di que no tienes suficiente información. 
Cita la fuente y el número de página de donde proviene la información.

CONTEXTO:
{context}

PREGUNTA: {question}

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
    
    # 6. Formatear la salida
    respuesta = resultado['result']
    fuentes = resultado['source_documents']
    
    print("\n--- RESPUESTA GENERADA POR LLAMA ---")
    print(respuesta)
    
    print("\n--- FUENTES RECUPERADAS (Para verificación) ---")
    for i, doc in enumerate(fuentes):
        # Usamos Path para obtener solo el nombre del archivo
        source_path_full = doc.metadata.get('source', 'Desconocida')
        page = doc.metadata.get('page', 'N/A')
        
        source_name = Path(source_path_full).name
        
        print(f"[{i+1}] Fuente: {Path(source_name).name}, Página: {page}")
        # ⭐️ MOSTRAR UNA X CANTIDAD DE TEXTO DE LA FUENTE
        print(f"    Extracto (Primeros {EXTRACT_LENGTH} chars): {doc.page_content[:EXTRACT_LENGTH].strip()}...")
        print("-" * 40)
    return ""

def inicializar_rag_chain():
    """
    Inicializa todos los componentes de la cadena RAG (Embeddings, Chroma, Llama)
    para ser reutilizados en el bucle interactivo.
    """
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
            max_tokens=2048,
            n_ctx=CONTEXT_WINDOW,
            n_gpu_layers=N_GPU_LAYERS,
            n_batch=N_BATCH,
            verbose=False,
        )

        # 4. Crear la Cadena RAG (RetrievalQA)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={"k": 3}),
            chain_type_kwargs={"prompt": RAG_PROMPT},
            return_source_documents=True
        )
        
        return qa_chain

    except FileNotFoundError:
        print(f"Error: El modelo LLAMA no se encontró en la ruta: {LLAMA_MODEL_PATH}")
        print("Asegúrate de que la variable LLAMA_MODEL_PATH sea correcta.")
        return None
    except Exception as e:
        print(f"Ocurrió un error durante la inicialización RAG: {e}")
        return None


if __name__ == "__main__":
    # Inicializar la cadena RAG una sola vez
    qa_chain = inicializar_rag_chain()
    
    if qa_chain is None:
        exit() # Salir si la inicialización falló

    # --- BUCLE INTERACTIVO ---
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