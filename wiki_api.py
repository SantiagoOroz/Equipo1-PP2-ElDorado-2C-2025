import requests
import wikitextparser as wtp
from time import sleep # Importamos sleep

class WikiAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False

    def login(self):
        # ... (Tu código de login - sin cambios)
        token_url = f"{self.base_url}/api.php"
        params = { "action": "query", "meta": "tokens", "type": "login", "format": "json" }
        response = self.session.get(token_url, params=params)
        data = response.json()
        login_token = data["query"]["tokens"]["logintoken"]

        payload = { "action": "login", "lgname": self.username, "lgpassword": self.password, "lgtoken": login_token, "format": "json" }
        login_response = self.session.post(token_url, data=payload)
        result = login_response.json()
        if result["login"]["result"] == "Success":
            self.logged_in = True
            print("✅ Login exitoso a la Wiki")
        else:
            raise Exception(f"Error al iniciar sesión: {result['login']['result']}")

    def ensure_login(self):
        if not self.logged_in:
            self.login()

    # --- NUEVA FUNCIÓN NECESARIA PARA LA INDEXACIÓN ---
    def get_all_page_titles(self):
        """
        Obtiene los títulos de TODAS las páginas de la wiki 
        usando 'list=allpages' (maneja la paginación).
        """
        self.ensure_login()
        all_titles = []
        apcontinue = None
        
        print("Buscando todos los títulos de página de la Wiki...")

        while True:
            params = {
                "action": "query",
                "list": "allpages",
                "aplimit": "max",
                "apfilterredir": "nonredirects", # Solo páginas, no redirecciones
                "format": "json"
            }
            if apcontinue:
                params["apcontinue"] = apcontinue

            r = self.session.get(f"{self.base_url}/api.php", params=params)
            data = r.json()
            
            for page in data.get("query", {}).get("allpages", []):
                all_titles.append(page["title"])
            
            if "continue" in data and "apcontinue" in data["continue"]:
                apcontinue = data["continue"]["apcontinue"]
                print(f"  ...encontrados {len(all_titles)} títulos. Continuando...")
                sleep(0.5)
            else:
                break
                
        print(f"🎉 Búsqueda de títulos completa. Total de páginas: {len(all_titles)}")
        return all_titles

    # --- (Funciones existentes - sin cambios) ---
    
    def search_pages(self, query, limit=5):
        # ... (sin cambios)
        self.ensure_login()
        params = { "action": "query", "list": "search", "srsearch": query, "srlimit": limit, "format": "json" }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def get_page_summary(self, title):
        # ... (sin cambios)
        self.ensure_login()
        params = { "action": "query", "prop": "extracts", "exintro": True, "explaintext": True, "titles": title, "redirects": 1, "format": "json" }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def get_page_raw_content(self, title):
        # ... (sin cambios)
        self.ensure_login()
        params = { "action": "query", "prop": "revisions", "rvprop": "content", "titles": title, "redirects": 1, "format": "json" }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def get_page_full_text(self, title):
        """
        Obtener el contenido completo de una página en formato de texto plano.
        (Tu versión robusta de Intento 1 + Intento 2)
        """
        self.ensure_login()
        
        # --- INTENTO 1: Método 'extracts' (limpio) ---
        params_extract = {
            "action": "query", "prop": "extracts", "explaintext": True, 
            "titles": title, "redirects": 1, "format": "json"
        }
        
        try:
            r_extract = self.session.get(f"{self.base_url}/api.php", params=params_extract)
            data_extract = r_extract.json()
            pages = data_extract.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]

            if page_id != "-1":
                content = pages[page_id].get("extract", "")
                if content and len(content.strip()) > 0:
                    return data_extract
        except Exception as e:
            print(f"Error en el Intento 1 (extracts): {e}")

        # --- INTENTO 2: Método 'revisions' (fuerza bruta) + Limpieza ---
        print(f"  -> 'extracts' falló para '{title}'. Probando 'revisions' (fuerza bruta)...")
        try:
            data_raw = self.get_page_raw_content(title)
            pages = data_raw.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]
            
            if page_id != "-1":
                raw_wikitext = pages[page_id].get("revisions", [{}])[0].get("*", "")
                if raw_wikitext:
                    cleaned_text = wtp.parse(raw_wikitext).plain_text()
                    pages[page_id]["extract"] = cleaned_text
                    return data_raw
        except Exception as e:
            print(f"Error en el Intento 2 (revisions): {e}")

        print(f"  -> Ambos métodos fallaron para '{title}'. Devolviendo json con contenido vacío.")
        return {"query": {"pages": {"-1": {}}}}