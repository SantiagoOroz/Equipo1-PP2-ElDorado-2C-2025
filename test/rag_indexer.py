# rag_indexer.py
"""
Extraer, limpiar, fragmentar y vectorizar PDFs brutos para crear la base de datos ChromaDB. 
"""

import re
import os
import glob
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

# --- CONFIGURACIÓN ---
PDF_DIR = r"data\raw\Antecedentes PDF"  # La carpeta donde están los 27 PDFs
CHROMA_DIR = "data/processed/chroma_db"  # Directorio para guardar el índice vectorial
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" # Modelo de embeddings de código abierto (local)

# --- FUNCIÓN DE LIMPIEZA DE TEXTO ---

def limpiar_texto_documento(doc: Document) -> Document:
    """
    Corrige problemas de extracción de PDF (palabras divididas por guiones y saltos 
    de línea internos) en un objeto Document. Mantiene los metadatos de la página.
    """
    texto = doc.page_content

    # 1. Unir palabras divididas por guion al final de línea
    # Busca: [letra o número][guion][-][salto de línea] (Ej: 'valo-\nramos')
    texto_unido = re.sub(r'(\w+)-\s*\n(\w+)', r'\1\2', texto, flags=re.MULTILINE)
    
    # 2. Eliminar saltos de línea simples y reemplazarlos por un espacio
    # Esto une líneas dentro de un mismo párrafo, pero conserva la estructura si el 
    # extractor original usó \n\n para párrafos.
    texto_limpio = texto_unido.replace('\n', ' ').replace('  ', ' ') 

    doc.page_content = texto_limpio
    return doc

# --- PIPELINE COMPLETO DE INDEXACIÓN ---

def indexar_lote_pdfs():
    """
    Ejecuta el pipeline RAG: Carga, Limpieza, Fragmentación y Almacenamiento Vectorial.
    """
    # 1. Búsqueda de Archivos
    # Usa glob para encontrar todos los archivos .pdf en el directorio 'raw'
    pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"Error: No se encontraron archivos PDF en el directorio: '{PDF_DIR}'")
        print("Asegúrate de que la carpeta 'raw' exista y contenga archivos PDF.")
        return

    all_chunks = []
    print(f"Iniciando el procesamiento de {len(pdf_files)} archivos en '{PDF_DIR}'...")

    # 2. Bucle de Procesamiento (Carga, Limpieza, Fragmentación)
    for i, file_path in enumerate(pdf_files):
        print(f"  > Procesando {i+1}/{len(pdf_files)}: {os.path.basename(file_path)}...")
        
        # 2.1 Carga (Extracción)
        loader = PyPDFLoader(file_path)
        documentos = loader.load()

        # 2.2 Limpieza de Texto
        documentos_limpios = [limpiar_texto_documento(doc) for doc in documentos]

        # 2.3 Fragmentación (Chunking)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks_pdf_actual = text_splitter.split_documents(documentos_limpios)
        all_chunks.extend(chunks_pdf_actual)
        
    print(f"\nProcesamiento de Lote Finalizado. Total de Chunks creados: {len(all_chunks)}")

    # 3. Vectorización y Persistencia (Almacenamiento Vectorial)
    print(f"3. Vectorizando y guardando en ChromaDB en el directorio: '{CHROMA_DIR}'...")
    
    # Crea el modelo de embeddings
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    # Crea y persiste el índice vectorial con todos los chunks
    # Esto guarda los vectores, el texto limpio y los metadatos (incluyendo la página)
    db = Chroma.from_documents(
        documents=all_chunks, 
        embedding=embeddings, 
        persist_directory=CHROMA_DIR
    )
    db.persist()
    print("¡Indexación completada con éxito! El índice está listo para consultas.")

if __name__ == "__main__":
    # Asegura que la carpeta de PDFs exista
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        print(f"Se ha creado la carpeta '{PDF_DIR}'. Coloca tus PDFs aquí y vuelve a ejecutar.")
    else:
        indexar_lote_pdfs()