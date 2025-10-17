# scripts/indexing.py
import os
import fitz  # PyMuPDF
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN (leída desde .env) ---
PDF_DIR = os.getenv("PDF_DIR")
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
CHROMA_DIR = os.getenv("CHROMA_DIR")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

def load_documents(source_dirs: list) -> list:
    """Carga todos los documentos PDF de una lista de directorios."""
    all_docs = []
    for directory in source_dirs:
        if not os.path.isdir(directory):
            print(f"Advertencia: El directorio '{directory}' no existe.")
            continue
        
        pdf_paths = list(Path(directory).glob("*.pdf"))
        print(f"Encontrados {len(pdf_paths)} PDFs en '{directory}'")
        for pdf_path in pdf_paths:
            try:
                loader = PyMuPDFLoader(str(pdf_path))
                docs = loader.load()
                # Añadir el número de página a los metadatos de cada documento
                for i, doc in enumerate(docs):
                    doc.metadata['page'] = i + 1
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error cargando el archivo {pdf_path}: {e}")
    return all_docs

def split_documents(docs: list) -> list:
    """Divide los documentos en fragmentos (chunks)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )
    return text_splitter.split_documents(docs)

def create_and_persist_index():
    """
    Función principal que orquesta la creación del índice vectorial.
    Lee los PDFs, los divide y los guarda en ChromaDB.
    """
    print("--- INICIANDO PROCESO DE INDEXACIÓN ---")
    
    # 1. Cargar documentos de ambos directorios
    source_directories = [PDF_DIR, UPLOAD_DIR]
    documents = load_documents(source_directories)
    
    if not documents:
        print("No se encontraron documentos para indexar. Proceso cancelado.")
        return {"ok": False, "error": "No se encontraron PDFs."}

    # 2. Dividir documentos en chunks
    chunks = split_documents(documents)
    print(f"Total de documentos: {len(documents)}, Total de chunks: {len(chunks)}")
    
    if not chunks:
        print("No se generaron chunks a partir de los documentos. Proceso cancelado.")
        return {"ok": False, "error": "No se pudo dividir los documentos en fragmentos."}

    # 3. Crear embeddings y persistir en ChromaDB
    print(f"Creando embeddings con el modelo: '{EMBEDDING_MODEL_NAME}'...")
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # Crear la base de datos vectorial
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"--- INDEXACIÓN COMPLETADA ---")
    print(f"Base de datos vectorial guardada en: '{CHROMA_DIR}'")
    return {"ok": True, "docs": len(documents), "chunks": len(chunks)}