import requests
import json
import os
from time import sleep
from dotenv import load_dotenv # ⬅️ Importamos la biblioteca para leer .env

# La clase WikiAPI existente (sin cambios funcionales, solo la reordené)
class WikiAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False
    
    # Métodos de la API (login, get_all_page_titles, get_page_content, etc.)
    
    def login(self):
        # Paso 1: obtener token de login
        token_url = f"{self.base_url}/api.php"
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json"
        }
        try:
            response = self.session.get(token_url, params=params)
            response.raise_for_status() # Lanza un error para códigos HTTP 4xx/5xx
            data = response.json()
            login_token = data["query"]["tokens"]["logintoken"]

            # Paso 2: hacer login
            payload = {
                "action": "login",
                "lgname": self.username,
                "lgpassword": self.password,
                "lgtoken": login_token,
                "format": "json"
            }
            login_response = self.session.post(token_url, data=payload)
            login_response.raise_for_status()
            result = login_response.json()

            if result["login"]["result"] == "Success":
                self.logged_in = True
                print("✅ Login exitoso a la Wiki")
            else:
                raise Exception(f"Error al iniciar sesión: {result['login']['result']}")
        except requests.exceptions.RequestException as e:
             raise Exception(f"Error de conexión con la Wiki: {e}")
        except KeyError:
             raise Exception("Error: Respuesta de la API de Wiki malformada. ¿Es la URL correcta?")

    def get_all_page_titles(self):
        """
        Obtiene los títulos de todas las páginas de la wiki (maneja la paginación).
        """
        self.ensure_login()
        all_titles = []
        apcontinue = None
        
        print("Buscando todos los títulos de página...")

        while True:
            params = {
                "action": "query",
                "list": "allpages",
                "aplimit": "max",
                "apfilterredir": "nonredirects",
                "format": "json"
            }
            if apcontinue:
                params["apcontinue"] = apcontinue

            r = self.session.get(f"{self.base_url}/api.php", params=params)
            data = r.json()
            
            # Extraer títulos
            for page in data.get("query", {}).get("allpages", []):
                all_titles.append(page["title"])
            
            # Verificar si hay más páginas (continuación)
            if "continue" in data and "apcontinue" in data["continue"]:
                apcontinue = data["continue"]["apcontinue"]
                print(f"  ...encontrados {len(all_titles)} títulos. Continuando desde: {apcontinue}")
                sleep(0.5)
            else:
                break
                
        print(f"🎉 Búsqueda de títulos completa. Total de páginas encontradas: {len(all_titles)}")
        return all_titles

    def get_page_content(self, title):
        """Obtener contenido completo de una página"""
        self.ensure_login()
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "titles": title,
            "format": "json"
        }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def ensure_login(self):
        if not self.logged_in:
            self.login()

def extract_all_wiki_content(api_instance, output_file="wiki_extract.json"):
    """
    Función principal para extraer todos los datos y guardarlos en un archivo JSON.
    """
    all_titles = api_instance.get_all_page_titles()
    all_content = {}
    
    print("\nIniciando extracción de contenido para cada página...")
    
    for i, title in enumerate(all_titles):
        print(f"[{i+1}/{len(all_titles)}] Extrayendo: **{title}**")
        
        try:
            content_json = api_instance.get_page_content(title)
            
            # Navegar a través de la estructura anidada de la respuesta de MediaWiki
            pages = content_json.get("query", {}).get("pages", {})
            page_id = next(iter(pages))
            revisions = pages.get(page_id, {}).get("revisions", [])
            
            if revisions:
                content = revisions[0].get("*")
                
                all_content[title] = {
                    "title": title,
                    "wiki_content": content
                }
            else:
                # Caso de página vacía o sin contenido de revisión
                all_content[title] = {"error": "No se encontró contenido de revisión"}

            sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error al extraer contenido de '{title}': {e}")
            all_content[title] = {"error": str(e)}

    # Guardar los resultados en un archivo JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_content, f, ensure_ascii=False, indent=4)

    print(f"\n✨ Extracción completa y guardada en **{output_file}**")
    print(f"Páginas procesadas: {len(all_content)}")
    return all_content

# --- Lógica Principal que usa el .env ---

if __name__ == '__main__':
    # 1. Cargar el archivo .env
    load_dotenv()
    
    # 2. Obtener las credenciales del entorno
    WIKI_URL = os.environ.get("WIKI_BASE_URL")
    WIKI_USERNAME = os.environ.get("WIKI_USERNAME")
    WIKI_PASSWORD = os.environ.get("WIKI_PASSWORD")
    
    # Usamos la variable de directorio del .env para el nombre del archivo de salida
    # aunque no es estrictamente necesario, es buena práctica.
    CHROMA_DIR = os.environ.get("CHROMA_DIR", "data/chroma_db")
    OUTPUT_FILENAME = os.path.join(os.path.dirname(CHROMA_DIR), "wiki_extract.json")

    # 3. Verificar que las credenciales existan
    if not all([WIKI_URL, WIKI_USERNAME, WIKI_PASSWORD]):
        print("🚨 Error: Faltan una o más credenciales (WIKI_BASE_URL, WIKI_USERNAME, WIKI_PASSWORD) en el archivo .env.")
    else:
        try:
            # 4. Inicializar y Ejecutar
            wiki_api = WikiAPI(WIKI_URL, WIKI_USERNAME, WIKI_PASSWORD)
            print(f"Usando URL de Wiki: {WIKI_URL}")
            
            wiki_data = extract_all_wiki_content(wiki_api, OUTPUT_FILENAME)
            
        except Exception as e:
            print(f"\n🚨 Terminación del script debido a un error: {e}")