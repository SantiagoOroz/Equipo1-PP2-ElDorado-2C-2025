import os
import shutil
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from wiki_api import WikiAPI
import gc
import stat
import uuid
import datetime
import traceback

load_dotenv()

PDF_DIR = os.getenv("PDF_DIR", "data/pdfs")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
LEGACY_CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
CHROMA_POINTER_FILE = str(Path(LEGACY_CHROMA_DIR).parent / (Path(LEGACY_CHROMA_DIR).name + "_active.txt"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

# cuantos versions mantener (opcional)
KEEP_VERSIONS = int(os.getenv("KEEP_CHROMA_VERSIONS", 3))


def limpiar_wikitexto(texto: str) -> str:
    if not texto:
        return ""
    texto = re.sub(r"\[\[(?:[^\]]+\|)?([^\]]+)\]\]", r"\1", texto)
    texto = re.sub(r"\{\{.+?\}\}", "", texto, flags=re.DOTALL)
    texto = re.sub(r"'{2,}([^']+)'{2,}", r"\1", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"={2,}\s*([^=]+)\s*={2,}", r"\n\1\n", texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto.strip()


def limpiar_texto_documento(doc: Document) -> Document:
    if not isinstance(doc, Document) or not hasattr(doc, 'page_content'):
        print(f"Advertencia: Se recibió un objeto inesperado para limpiar: {type(doc)}")
        return doc
    texto = doc.page_content
    texto_unido = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto, flags=re.MULTILINE)
    texto_plano = texto_unido.replace('\n', ' ')
    texto_limpio = re.sub(r'[\s\t\xa0]+', ' ', texto_plano).strip()
    doc.page_content = texto_limpio
    return doc


def load_documents(source_dirs: list) -> list:
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


def load_wiki_documents(wiki: WikiAPI) -> list:
    print("Iniciando extracción de contenido de la Wiki...")
    all_wiki_docs = []
    try:
        titles = wiki.get_all_page_titles()
        if not titles:
            print("No se encontraron páginas en la Wiki.")
            return []
        for i, title in enumerate(titles):
            print(f"  [{i+1}/{len(titles)}] Extrayendo: {title}")
            full_data = wiki.get_page_full_text(title)
            page_id = list(full_data.get("query", {}).get("pages", {}).keys())[0]
            if page_id and page_id != "-1":
                content_potencialmente_sucio = full_data["query"]["pages"][page_id].get("extract", "")
                content = limpiar_wikitexto(content_potencialmente_sucio)
                if content and content.strip():
                    doc = Document(page_content=content, metadata={"source": title, "type": "wiki"})
                    all_wiki_docs.append(doc)
                else:
                    print(f"  -> Advertencia: Artículo '{title}' está vacío después de la limpieza. Omitiendo.")
        print(f"Extracción de Wiki completa. {len(all_wiki_docs)} páginas con contenido.")
        return all_wiki_docs
    except Exception as e:
        print(f"Error fatal durante la extracción de la Wiki: {e}")
        return []


def split_documents(docs: list) -> list:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len)
    return text_splitter.split_documents(docs)


def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"on_rm_error: no se pudo borrar {path}: {e}")


def _prune_old_versions(base_parent: Path, base_name: str, keep=KEEP_VERSIONS):
    """
    Mantener solo las últimas `keep` versiones y borrar el resto (si se puede).
    """
    try:
        candidates = sorted([d for d in base_parent.glob(base_name + "_v*") if d.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        to_delete = candidates[keep:]
        for d in to_delete:
            try:
                print("Pruning: eliminando versión antigua:", d)
                shutil.rmtree(d, onerror=on_rm_error)
            except Exception as e:
                print("Prune: no se pudo eliminar", d, e)
    except Exception as e:
        print("Prune error:", e)


def create_and_persist_index():
    print("--- INICIANDO PROCESO DE INDEXACIÓN ---")

    base_parent = Path(LEGACY_CHROMA_DIR).parent
    base_name = Path(LEGACY_CHROMA_DIR).name

    uid = uuid.uuid4().hex[:8]
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    new_dir = base_parent / f"{base_name}_v{ts}_{uid}"

    # Asegurar limpieza previa
    if new_dir.exists():
        try:
            shutil.rmtree(new_dir, onerror=on_rm_error)
        except Exception:
            pass
    os.makedirs(new_dir, exist_ok=True)

    source_directories = [PDF_DIR, UPLOAD_DIR]
    documents_pdf = load_documents(source_directories)

    if not all([os.getenv("WIKI_BASE_URL"), os.getenv("WIKI_USERNAME"), os.getenv("WIKI_PASSWORD")]):
        print("Advertencia: Faltan credenciales de Wiki en .env. Omitiendo indexación de Wiki.")
        documents_wiki = []
    else:
        try:
            wiki = WikiAPI(os.getenv("WIKI_BASE_URL"), os.getenv("WIKI_USERNAME"), os.getenv("WIKI_PASSWORD"))
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

    db = None
    try:
        # Crear la DB en la carpeta nueva (nunca tocamos la carpeta activa)
        print("Creando índice en:", new_dir)
        db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=str(new_dir))
        # intentamos persist por compatibilidad
        try:
            if hasattr(db, "persist"):
                db.persist()
        except Exception:
            pass

        # cerrar cliente si existe
        try:
            client = getattr(db, "client", None)
            if client and hasattr(client, "close"):
                client.close()
        except Exception:
            pass

        del db
        gc.collect()
        time.sleep(0.8)  # permitimos que OS libere handles

        # Verificar que index files existan
        has_expected = any(new_dir.glob("**/*"))
        if not has_expected:
            raise Exception(f"No se detectaron archivos dentro de {new_dir} tras crear el índice.")

        # Actualizar puntero: escribir atómico
        pointer = Path(CHROMA_POINTER_FILE)
        tmp = pointer.with_suffix(".tmp")
        # escribir ruta relativa (relativa al parent) para portabilidad
        rel_path = new_dir.relative_to(base_parent)
        tmp.write_text(str(rel_path), encoding="utf-8")
        os.replace(str(tmp), str(pointer))
        print("Puntero actualizado a:", new_dir)

        # Prune de versiones antiguas en background (intento simple)
        _prune_old_versions(base_parent, base_name, keep=KEEP_VERSIONS)

    except Exception as e:
        print(f"Error creando índice en {new_dir}: {e}")
        traceback.print_exc()
        # intentar limpiar carpeta nueva si se creó parcialmente
        try:
            if new_dir.exists():
                shutil.rmtree(new_dir, onerror=on_rm_error)
        except Exception:
            pass
        return {"ok": False, "error": str(e)}

    print(f"--- INDEXACIÓN COMPLETADA ---")
    print(f"Nuevo índice guardado en: '{new_dir}'")
    return {"ok": True, "new_index": str(new_dir), "chunks": len(chunks)}


if __name__ == "__main__":
    res = create_and_persist_index()
    print("RESULT:", res)
    if not res.get("ok"):
        raise SystemExit(1)
