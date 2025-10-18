"""
Módulo: wiki_api.py
Proyecto: Chatbot El Dorado
Autor: Equipo 1 - PP2 2C 2025

Este script permite conectarse a la API de MediaWiki utilizada por la empresa El Dorado,
realizando el proceso de autenticación (login) con las credenciales oficiales del proyecto.

Funciones principales:
- get_login_token(): obtiene el token necesario para iniciar sesión.
- do_login(): realiza el login con las credenciales almacenadas en el archivo .env.
"""

import os
import requests
from dotenv import load_dotenv

# URL base de la API de MediaWiki de El Dorado
API_URL = "https://objetivos.eldoradosrl.ar/wiki/api.php"

def debug(msg):
    """
    Función auxiliar para imprimir mensajes de depuración con un formato uniforme.
    """
    print(f"[wiki_client] {msg}", flush=True)

def get_session():
    """
    Crea y devuelve una sesión HTTP reutilizable.
    Esto permite mantener las cookies entre llamadas (por ejemplo, tras el login).
    """
    return requests.Session()

def get_login_token(session):
    """
    Solicita el token de inicio de sesión (login token) requerido por la API.
    Este token previene ataques CSRF y debe obtenerse antes de hacer login.
    """
    r = session.get(API_URL, params={
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    })
    r.raise_for_status()  # Si la solicitud falla, lanza una excepción
    data = r.json()
    return data["query"]["tokens"]["logintoken"]

def do_login(session, user, password):
    """
    Realiza el inicio de sesión utilizando las credenciales del usuario.
    Devuelve la respuesta JSON completa de la API.
    """
    token = get_login_token(session)
    r = session.post(API_URL, data={
        "action": "login",
        "format": "json",
        "lgname": user,
        "lgpassword": password,
        "lgtoken": token
    })
    r.raise_for_status()
    return r.json()

# ----------------------------------------------------------------------
# FUNCIONES DE CONSULTA DE LA WIKI (LECTURA)
# ----------------------------------------------------------------------

def search(session, term: str) -> list[str]:
    """
    Realiza una búsqueda en la Wiki de El Dorado utilizando un término clave.
    Parámetros:
        session: sesión HTTP ya autenticada.
        term: palabra o frase a buscar (por ejemplo, "hormigón").
    Retorna:
        Una lista con los títulos de las páginas que coinciden con la búsqueda.
    """
    # Realiza una solicitud GET a la API con el parámetro 'srsearch' = término buscado
    r = session.get(API_URL, params={
        "action": "query",       # Acción: consultar datos
        "list": "search",        # Tipo de consulta: búsqueda
        "srsearch": term,        # Palabra clave a buscar
        "srlimit": 10,           # Cantidad máxima de resultados
        "format": "json"         # Formato de respuesta
    })
    # Si ocurre un error HTTP, levanta una excepción
    r.raise_for_status()

    # Devuelve una lista con los títulos de los resultados encontrados
    return [item["title"] for item in r.json()["query"]["search"]]


def get_content(session, title: str) -> str:
    """
    Obtiene el contenido (texto) de una página específica en la Wiki.
    Parámetros:
        session: sesión HTTP ya autenticada.
        title: título exacto de la página a consultar.
    Retorna:
        El contenido de la página en formato wikitexto.
    """
    # Solicitud GET a la API con el título de la página
    r = session.get(API_URL, params={
        "action": "query",        # Acción: consultar datos
        "prop": "revisions",      # Propiedad: revisar versiones de la página
        "rvprop": "content",      # Especifica que se quiere obtener el contenido
        "rvslots": "main",        # En versiones modernas, el contenido está en el "slot main"
        "titles": title,          # Título de la página
        "format": "json"          # Formato de respuesta
    })
    # Verifica si hubo error HTTP
    r.raise_for_status()

    # Extrae el contenido de la respuesta JSON de la API
    pages = r.json()["query"]["pages"]                # Accede al bloque 'pages'
    page = next(iter(pages.values()))                 # Obtiene el primer resultado
    rev = (page.get("revisions") or [{}])[0]          # Accede a la revisión principal
    # Retorna el contenido según la estructura de la versión de MediaWiki
    return rev.get("slots", {}).get("main", {}).get("*") or rev.get("*") or ""


# ----------------------------------------------------------------------
# BLOQUE PRINCIPAL
# ----------------------------------------------------------------------
# Este bloque se ejecuta únicamente si el archivo se corre directamente.
# Permite probar manualmente las funciones de login, búsqueda y lectura.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        # Cargar las variables desde el archivo .env (usuario y contraseña)
        debug("Cargando variables desde el archivo .env...")
        load_dotenv()
        user = os.getenv("WIKI_USER")
        pwd  = os.getenv("WIKI_PASSWORD")

        # Mostrar en consola qué usuario se está utilizando (sin mostrar la contraseña)
        debug(f"WIKI_USER={user!r} | WIKI_PASSWORD={'***' if pwd else None}")

        # Verificar que ambas variables existan, sino finalizar el programa
        if not user or not pwd:
            raise SystemExit("Faltan variables en .env (WIKI_USER / WIKI_PASSWORD).")

        # Crear una nueva sesión HTTP (mantiene cookies y tokens)
        debug("Creando sesión HTTP...")
        session = get_session()

        # Iniciar sesión en la Wiki de El Dorado
        debug("Intentando login en la Wiki de El Dorado...")
        resp = do_login(session, user, pwd)
        debug(f"Respuesta del login: {resp}")

        # ---- PRUEBA DE FUNCIONALIDAD ----
        # Buscar páginas que contengan el término "hormigón"
        term = "hormigón"
        debug(f"Buscando páginas que coincidan con: {term!r} ...")
        titles = search(session, term)
        debug(f"Títulos encontrados: {titles[:5]}")  # muestra los primeros 5 títulos

        # Si hay resultados, obtener el contenido de la primera página encontrada
        if titles:
            title = titles[0]
            debug(f"Obteniendo contenido de: {title!r} ...")
            content = get_content(session, title)

            # Mostrar un fragmento del contenido (solo los primeros 600 caracteres)
            debug(f"Primeros 600 caracteres del contenido:\n{content[:600]}")

    except Exception as e:
        # Si ocurre un error, lo muestra con el tipo de excepción
        debug(f"ERROR: {type(e).__name__}: {e}")
        raise

