"""
Extraer, limpiar, fragmentar y vectorizar PDFs brutos para crear la base de datos ChromaDB.
"""
import re
import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN (leída desde variables de entorno) ---
PDF_DIR = os.getenv("PDF_DIR", "data/raw/Antecedentes PDF")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/processed/chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")


# --- FUNCIÓN DE LIMPIEZA DE TEXTO ---
def limpiar_texto_documento(doc: Document) -> Document:
    """
    Corrige problemas de extracción de PDF (palabras divididas por guiones y saltos
    de línea internos) en un objeto Document, asegurando texto continuo.
    """
    texto = doc.page_content
    # 1. Unir palabras divididas por guion al final de línea (Ej: 'valo-\nramos')
    texto_unido = re.sub(r'(\w+)-\s*\n(\w+)', r'\1\2', texto, flags=re.MULTILINE)
    # 2. Reemplazar CUALQUIER salto de línea (simple o doble) por un espacio
    texto_plano = texto_unido.replace('\n', ' ')
    texto_limpio = re.sub(r'[\s\t\xa0]+', ' ', texto_plano).strip()
    doc.page_content = texto_limpio
    return doc


# --- PIPELINE COMPLETO DE INDEXACIÓN ---
def indexar_lote_pdfs():
    """
    Ejecuta el pipeline RAG: Carga, Limpieza, Fragmentación y Almacenamiento Vectorial.
    """
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"Error: No se encontraron archivos PDF en el directorio: '{PDF_DIR}'")
        print("Asegúrate de que la carpeta exista y contenga archivos PDF.")
        return

    all_chunks = []
    print(f"Iniciando el procesamiento de {len(pdf_files)} archivos en '{PDF_DIR}'...")

    for i, file_path in enumerate(pdf_files):
        print(f"  > Procesando {i+1}/{len(pdf_files)}: {os.path.basename(file_path)}...")
        loader = PyPDFLoader(file_path)
        documentos = loader.load()
        documentos_limpios = [limpiar_texto_documento(doc) for doc in documentos]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks_pdf_actual = text_splitter.split_documents(documentos_limpios)
        all_chunks.extend(chunks_pdf_actual)
        
    print(f"\nProcesamiento de Lote Finalizado. Total de Chunks creados: {len(all_chunks)}")

    print(f"Vectorizando y guardando en ChromaDB en el directorio: '{CHROMA_DIR}'...")
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    db = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    db.persist()
    print("¡Indexación completada con éxito! El índice está listo para consultas.")


if __name__ == "__main__":
    # Asegurarse de que el directorio de PDFs exista, si no, crearlo y pedir al usuario que agregue PDFs.
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        print(f"Se ha creado la carpeta '{PDF_DIR}'. Coloca tus PDFs aquí y vuelve a ejecutar.")
    else:
        indexar_lote_pdfs()