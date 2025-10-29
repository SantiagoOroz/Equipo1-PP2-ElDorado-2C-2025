import os
import shutil
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN (leída desde .env) ---
PDF_DIR = os.getenv("PDF_DIR", "data/pdfs")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))


# --- FUNCIÓN DE LIMPIEZA DE TEXTO ---
def limpiar_texto_documento(doc: Document) -> Document:
    """
    Corrige problemas de extracción de PDF (palabras divididas por guiones y saltos
    de línea internos) en un objeto Document, asegurando texto continuo.
    """
    if not isinstance(doc, Document) or not hasattr(doc, 'page_content'):
        print(f"Advertencia: Se recibió un objeto inesperado para limpiar: {type(doc)}")
        return doc

    texto = doc.page_content
    
    # 1. Unir palabras divididas por guion al final de línea (Ej: 'valo-\nramos' -> 'valoramos')
    texto_unido = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto, flags=re.MULTILINE)
    
    # 2. Reemplazar saltos de línea restantes por un espacio
    texto_plano = texto_unido.replace('\n', ' ')
    
    # 3. Eliminar espacios múltiples, tabulaciones, etc.
    texto_limpio = re.sub(r'[\s\t\xa0]+', ' ', texto_plano).strip()
    
    doc.page_content = texto_limpio
    return doc

def load_documents(source_dirs: list) -> list:
    """Carga todos los documentos PDF de una lista de directorios."""
    all_docs = []
    for directory in source_dirs:
        # Asegurarse que los directorios de entrada existan
        os.makedirs(directory, exist_ok=True)
        
        if not os.path.isdir(directory):
            print(f"Advertencia: El directorio '{directory}' no existe.")
            continue
        
        pdf_paths = list(Path(directory).glob("*.pdf"))
        print(f"Encontrados {len(pdf_paths)} PDFs en '{directory}'")
        
        for pdf_path in pdf_paths:
            try:
                loader = PyMuPDFLoader(str(pdf_path))
                docs = loader.load()
                
                cleaned_docs = []
                for i, doc in enumerate(docs):
                    # Añadir metadatos
                    doc.metadata['page'] = i + 1
                    doc.metadata['source'] = Path(pdf_path).name
                    
                    # Aplicar la limpieza
                    doc_limpio = limpiar_texto_documento(doc)
                    cleaned_docs.append(doc_limpio)
                
                all_docs.extend(cleaned_docs)
                
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
    Borra el índice anterior, lee los PDFs, los divide y los guarda en ChromaDB.
    """
    print("--- INICIANDO PROCESO DE INDEXACIÓN ---")
    
    # 1. Borrar índice antiguo si existe
    if os.path.exists(CHROMA_DIR):
        print(f"Borrando índice antiguo en: {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    
    # 2. Cargar y limpiar documentos
    # ESTA ES LA LÍNEA QUE DA EL ERROR SI LA FUNCIÓN DE ARRIBA NO EXISTE
    source_directories = [PDF_DIR, UPLOAD_DIR]
    documents = load_documents(source_directories)
    
    if not documents:
        print("No se encontraron documentos para indexar. Proceso cancelado.")
        return {"ok": False, "error": "No se encontraron PDFs."}

    # 3. Dividir documentos en chunks
    chunks = split_documents(documents)
    print(f"Total de documentos: {len(documents)}, Total de chunks: {len(chunks)}")
    
    if not chunks:
        print("No se generaron chunks a partir de los documentos. Proceso cancelado.")
        return {"ok": False, "error": "No se pudo dividir los documentos en fragmentos."}

    # 4. Crear embeddings y persistir en ChromaDB
    print(f"Creando embeddings con el modelo: '{EMBEDDING_MODEL_NAME}'...")
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"--- INDEXACIÓN COMPLETADA ---")
    print(f"Base de datos vectorial guardada en: '{CHROMA_DIR}'")
    return {"ok": True, "docs": len(documents), "chunks": len(chunks)}

if __name__ == "__main__":
    create_and_persist_index()