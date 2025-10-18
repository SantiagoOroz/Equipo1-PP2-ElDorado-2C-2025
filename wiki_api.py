import requests

class WikiAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False

    def login(self):
        # Paso 1: obtener token de login
        token_url = f"{self.base_url}/api.php"
        params = {
            "action": "query",
            "meta": "tokens",
            "type": "login",
            "format": "json"
        }
        response = self.session.get(token_url, params=params)
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

    def get_page_summary(self, title):
        """Obtener resumen introductorio"""
        self.ensure_login()
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title,
            "format": "json"
        }
        r = self.session.get(f"{self.base_url}/api.php", params=params)
        return r.json()

    def ensure_login(self):
        if not self.logged_in:
            self.login()
