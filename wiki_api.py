import requests
import wikitextparser as wtp # ⬅️ Importamos el parser

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


    def search_pages(self, query, limit=5):
        """Buscar páginas por palabra clave"""
        self.ensure_login()
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json"
        }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def get_page_summary(self, title):
        """Obtener resumen introductorio (también sigue redirecciones)"""
        self.ensure_login()
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title,
            "redirects": 1, # ⬅️ Añadido para seguir atajos
            "format": "json"
        }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def ensure_login(self):
        if not self.logged_in:
            self.login()

    def get_page_raw_content(self, title):
        """
        Método de 'fuerza bruta': obtiene el wikitexto crudo.
        """
        self.ensure_login()
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content", # Obtiene el contenido crudo (wikitext)
            "titles": title,
            "redirects": 1,      # Sigue redirecciones
            "format": "json"
        }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def get_page_full_text(self, title):
        """
        Obtener el contenido completo de una página en formato de texto plano.
        INTENTO 1: Usar 'prop=extracts' (método limpio y rápido).
        INTENTO 2: Si falla, usar 'prop=revisions' y limpiar el wikitexto.
        """
        self.ensure_login()
        
        # --- INTENTO 1: Método 'extracts' (limpio) ---
        params_extract = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True, 
            "titles": title,
            "redirects": 1,      # ⬅️ CLAVE: Sigue las redirecciones
            "format": "json"
        }
        
        try:
            r_extract = self.session.get(f"{self.base_url}/api.php", params=params_extract)
            data_extract = r_extract.json()
            pages = data_extract.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]

            if page_id != "-1":
                content = pages[page_id].get("extract", "")
                if content and len(content.strip()) > 0:
                    # ¡Éxito! Devolvemos el texto plano limpio
                    return data_extract
        except Exception as e:
            print(f"Error en el Intento 1 (extracts): {e}")
            # Continuar al Intento 2

        # --- INTENTO 2: Método 'revisions' (fuerza bruta) + Limpieza ---
        print(f"  -> 'extracts' falló para '{title}'. Probando 'revisions' (fuerza bruta)...")
        try:
            data_raw = self.get_page_raw_content(title) # Usa el nuevo método
            pages = data_raw.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]
            
            if page_id != "-1":
                # Obtener el wikitexto crudo
                raw_wikitext = pages[page_id].get("revisions", [{}])[0].get("*", "")
                
                if raw_wikitext:
                    # 💡 Limpiar el wikitexto usando la biblioteca
                    cleaned_text = wtp.parse(raw_wikitext).plain_text()
                    
                    # Reconstruir la estructura de 'extracts' para que app.py no falle
                    pages[page_id]["extract"] = cleaned_text
                    return data_raw # Devolvemos el JSON con el contenido limpio
                    
        except Exception as e:
            print(f"Error en el Intento 2 (revisions): {e}")

        # Si ambos fallan, devolvemos un JSON vacío compatible
        print(f"  -> Ambos métodos fallaron para '{title}'. Devolviendo json con contenido vacío.")
        return {"query": {"pages": {"-1": {}}}}