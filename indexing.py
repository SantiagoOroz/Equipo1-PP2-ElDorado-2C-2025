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

# IMPORTAMOS LA API DE LA WIKI
from wiki_api import WikiAPI

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN (leída desde .env) ---
PDF_DIR = os.getenv("PDF_DIR", "data/pdfs")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

# AÑADIMOS CREDENCIALES DE WIKI (necesarias para la indexación)
WIKI_BASE_URL = os.getenv("WIKI_BASE_URL")
WIKI_USERNAME = os.getenv("WIKI_USERNAME")
WIKI_PASSWORD = os.getenv("WIKI_PASSWORD")


# --- 💡 NUEVA FUNCIÓN DE LIMPIEZA DE WIKITEXTO ---
def limpiar_wikitexto(texto: str) -> str:
    """
    Limpia el wikitexto de forma más agresiva,
    eliminando los restos de formato más comunes.
    """
    if not texto:
        return ""
    
    # 1. Eliminar títulos (ej. ==Título==, ===Subtítulo===)
    #    Esto los convierte en texto plano.
    texto = re.sub(r"={2,}\s*([^=]+)\s*={2,}", r"\1\n", texto) 
    
    # 2. Eliminar enlaces internos [[Pagina|Texto a mostrar]] o [[Pagina]]
    #    Esto se queda con el "Texto a mostrar" o "Pagina"
    texto = re.sub(r"\[\[(?:[^\]]+\|)?([^\]]+)\]\]", r"\1", texto)
    
    # 3. Eliminar plantillas (ej. {{Plantilla}}) - esto las borra
    texto = re.sub(r"\{\{.+?\}\}", "", texto, flags=re.DOTALL)
    
    # 4. Eliminar viñetas y sangrías (ej. * item, : item, # item)
    texto = re.sub(r"^[*\#:]+\s*", "", texto, flags=re.MULTILINE)
    
    # 5. Eliminar formato básico (negrita, cursiva)
    texto = re.sub(r"'''([^']+)'''", r"\1", texto) # Negrita
    texto = re.sub(r"''([^']+)''", r"\1", texto)   # Cursiva

    # 6. Limpiar saltos de línea y espacios extra
    texto = re.sub(r"\n{3,}", "\n\n", texto) # Múltiples saltos a dos
    texto = re.sub(r"[\t\xa0]+", " ", texto).strip()
    
    return texto

# --- FUNCIÓN DE LIMPIEZA DE TEXTO (Sin cambios) ---
def limpiar_texto_documento(doc: Document) -> Document:
    # ... (Tu función de limpieza de PDF - sin cambios)
    if not isinstance(doc, Document) or not hasattr(doc, 'page_content'):
        print(f"Advertencia: Se recibió un objeto inesperado para limpiar: {type(doc)}")
        return doc
    texto = doc.page_content
    texto_unido = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto, flags=re.MULTILINE)
    texto_plano = texto_unido.replace('\n', ' ')
    texto_limpio = re.sub(r'[\s\t\xa0]+', ' ', texto_plano).strip()
    doc.page_content = texto_limpio
    return doc

# --- CARGA DE PDFs (Sin cambios) ---
def load_documents(source_dirs: list) -> list:
    # ... (Tu función de carga de PDF - sin cambios)
    all_docs = []
    for directory in source_dirs:
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
                    doc.metadata['page'] = i + 1
                    doc.metadata['source'] = Path(pdf_path).name
                    doc.metadata['type'] = 'pdf' 
                    doc_limpio = limpiar_texto_documento(doc)
                    cleaned_docs.append(doc_limpio)
                all_docs.extend(cleaned_docs)
            except Exception as e:
                print(f"Error cargando el archivo {pdf_path}: {e}")
    return all_docs

# --- 💡 MODIFICACIÓN: load_wiki_documents ---
def load_wiki_documents(wiki: WikiAPI) -> list:
    """
    Extrae todo el contenido de la Wiki y lo convierte en Documentos de LangChain.
    """
    print("Iniciando extracción de contenido de la Wiki...")
    all_wiki_docs = []
    
    try:
        # 1. Obtener todos los títulos
        titles = wiki.get_all_page_titles()
        if not titles:
            print("No se encontraron páginas en la Wiki.")
            return []

        # 2. Iterar y extraer contenido completo
        for i, title in enumerate(titles):
            print(f"  [{i+1}/{len(titles)}] Extrayendo: {title}")
            
            full_data = wiki.get_page_full_text(title)
            page_id = list(full_data.get("query", {}).get("pages", {}).keys())[0]

            if page_id and page_id != "-1":
                # 'content' puede venir sucio del parser (intento 2) o de 'extracts' (intento 1)
                content_potencialmente_sucio = full_data["query"]["pages"][page_id].get("extract", "")
                
                # 💡💡 PASO DE LIMPIEZA ADICIONAL Y AGRESIVO 💡💡
                content = limpiar_wikitexto(content_potencialmente_sucio) 
                
                if content and content.strip():
                    # 3. Crear el Documento de LangChain
                    doc = Document(
                        page_content=content, # ⬅️ Usamos el contenido 100% limpio
                        metadata={
                            "source": title, # El "nombre" del archivo es el título
                            "type": "wiki"   # CLAVE para diferenciar en el frontend
                        }
                    )
                    all_wiki_docs.append(doc)
                else:
                    print(f"  -> Advertencia: Artículo '{title}' está vacío después de la limpieza. Omitiendo.")
        
        print(f"Extracción de Wiki completa. {len(all_wiki_docs)} páginas con contenido.")
        return all_wiki_docs

    except Exception as e:
        print(f"Error fatal durante la extracción de la Wiki: {e}")
        return []


# --- FUNCIÓN DE SPLIT (Sin cambios) ---
def split_documents(docs: list) -> list:
    # ... (Tu función de split - sin cambios)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )
    return text_splitter.split_documents(docs)


# --- FUNCIÓN PRINCIPAL (Sin cambios) ---
def create_and_persist_index():
    # ... (Tu función create_and_persist_index - sin cambios)
    print("--- INICIANDO PROCESO DE INDEXACIÓN ---")
    
    if os.path.exists(CHROMA_DIR):
        print(f"Borrando índice antiguo en: {CHROMA_DIR}")
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    
    source_directories = [PDF_DIR, UPLOAD_DIR]
    documents_pdf = load_documents(source_directories)
    
    if not all([WIKI_BASE_URL, WIKI_USERNAME, WIKI_PASSWORD]):
        print("Advertencia: Faltan credenciales de Wiki en .env. Omitiendo indexación de Wiki.")
        documents_wiki = []
    else:
        try:
            print(f"Conectando a {WIKI_BASE_URL} para indexar...")
            wiki = WikiAPI(WIKI_BASE_URL, WIKI_USERNAME, WIKI_PASSWORD)
            wiki.login()
            documents_wiki = load_wiki_documents(wiki)
        except Exception as e:
            print(f"Error al conectar o extraer de la Wiki: {e}")
            documents_wiki = []
            
    all_documents = documents_pdf + documents_wiki
    
    if not all_documents:
        print("No se encontraron documentos (ni PDF ni Wiki) para indexar. Proceso cancelado.")
        return {"ok": False, "error": "No se encontraron documentos."}

    chunks = split_documents(all_documents)
    print(f"Total de documentos (PDFs+Wiki): {len(all_documents)}, Total de chunks: {len(chunks)}")
    
    if not chunks:
        print("No se generaron chunks. Proceso cancelado.")
        return {"ok": False, "error": "No se pudo dividir los documentos en fragmentos."}

    print(f"Creando embeddings con el modelo: '{EMBEDDING_MODEL_NAME}'...")
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"--- INDEXACIÓN COMPLETADA ---")
    print(f"Base de datos vectorial guardada en: '{CHROMA_DIR}'")
    return {"ok": True, "docs": len(all_documents), "chunks": len(chunks)}

if __name__ == "__main__":
    create_and_persist_index()