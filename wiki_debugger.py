import os
import re
import requests
from dotenv import load_dotenv
from wiki_api import WikiAPI # Importamos tu clase existente

# --- Cargar variables de entorno ---
load_dotenv()

# --- CONFIGURACIÓN (leída desde .env) ---
WIKI_BASE_URL = os.getenv("WIKI_BASE_URL")
WIKI_USERNAME = os.getenv("WIKI_USERNAME")
WIKI_PASSWORD = os.getenv("WIKI_PASSWORD")

# --- FUNCIONES DE LIMPIEZA COPIADAS DE INDEXING.PY ---

def limpiar_wikitexto(texto: str) -> str:
    """
    Limpia el wikitexto de forma menos agresiva (tu última versión).
    """
    if not texto:
        return ""
    
    # 1. Eliminar enlaces internos [[Pagina|Texto a mostrar]] o [[Pagina]]
    texto = re.sub(r"\[\[(?:[^\]]+\|)?([^\]]+)\]\]", r"\1", texto)
    
    # 2. Eliminar plantillas (ej. {{Plantilla}}) - esto las borra
    texto = re.sub(r"\{\{.+?\}\}", "", texto, flags=re.DOTALL)
    
    # 3. Eliminar formato básico (negrita, cursiva) - '''texto'''
    texto = re.sub(r"'''([^']+)'''", r"\1", texto) 
    texto = re.sub(r"''([^']+)''", r"\1", texto)   

    # 4. Eliminar tags HTML (a veces quedan restos como <ref>, <div>)
    texto = re.sub(r"<[^>]+>", "", texto) 

    # 5. Limpiar espacios múltiples y saltos de línea excesivos
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    texto = re.sub(r"[\t\xa0]+", " ", texto).strip()
    
    return texto


def debug_wiki_page(wiki: WikiAPI, title: str):
    """
    Extrae el contenido crudo, aplica la limpieza y lo imprime.
    """
    print(f"=======================================================")
    print(f"|  DEBUG de la página: {title}  |")
    print(f"=======================================================")
    
    try:
        # Usamos tu método robusto (Intento 1 y 2) para extraer
        full_data = wiki.get_page_full_text(title) 
        page_id = list(full_data.get("query", {}).get("pages", {}).keys())[0]

        if page_id and page_id != "-1":
            content_potencialmente_sucio = full_data["query"]["pages"][page_id].get("extract", "")
            
            if not content_potencialmente_sucio:
                print("ERROR: Contenido extraído de la Wiki está VACÍO (revisar get_page_full_text).")
                return
            
            # 1. Aplicamos la limpieza que usa indexing.py
            content_limpio = limpiar_wikitexto(content_potencialmente_sucio)
            
            print("\n--- A. CONTENIDO CRUDO (antes de limpiar_wikitexto) ---\n")
            print(content_potencialmente_sucio[:1000] + "...\n")
            
            print("--- B. CONTENIDO LIMPIO (Lo que se guarda en ChromaDB) ---\n")
            print(content_limpio)
            
        else:
            print(f"Página no encontrada o ID inválido (-1).")

    except Exception as e:
        print(f"Error al procesar la página {title}: {e}")

if __name__ == "__main__":
    if not all([WIKI_BASE_URL, WIKI_USERNAME, WIKI_PASSWORD]):
        print("🚨 Error: Faltan credenciales de Wiki en el archivo .env.")
        exit()

    try:
        # Inicializar la API y forzar el login
        wiki_api = WikiAPI(WIKI_BASE_URL, WIKI_USERNAME, WIKI_PASSWORD)
        wiki_api.login()
        
        # --- Páginas a Debuggear ---
        PAGES_TO_DEBUG = ["Vendedor", "Gerencia general", "Jefatura de administración"] 
        
        for page_title in PAGES_TO_DEBUG:
            debug_wiki_page(wiki_api, page_title)
            
    except Exception as e:
        print(f"\n🚨 Terminación del script debido a un error: {e}")