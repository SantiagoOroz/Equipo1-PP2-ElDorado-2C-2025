# Asistente Técnico RAG - El Dorado SRL
![Portada](frontend/public/El_dorado_portada.jpg)
<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

## Grupo 1 de Practicas Profesionalizantes II junto a la empresa El Dorado.
Este repositorio contiene el código para un asistente técnico de chat basado en RAG (Retrieval-Augmented Generation). Fue desarrollado por el **Equipo 1** de las Prácticas Profesionalizantes 2 (PP2) del **Centro Politécnico Malvinas Argentinas**, durante el segundo cuatrimestre de 2025.

El asistente responde preguntas basándose en una base de conocimiento interna compuesta por documentos PDF y una instancia de MediaWiki de la empresa El Dorado SRL.

## 📖 Guía de Usuario

Para una guía detallada sobre cómo usar la aplicación, acceder al panel de administrador y gestionar la base de conocimiento, consulta la **[Guía de Usuario completa aquí](https://cristiancouto.github.io/eldoradosrl.github.io/#/guia-usuario)**.

## 🚀 Características Principales

* **Chat con RAG**: Responde preguntas utilizando un LLM local (vía LM Studio) alimentado con contexto de documentos internos.
* **Base de Conocimiento Dual**: Indexa y busca información tanto en **archivos PDF** como en una **Wiki** interna (MediaWiki).
* **Entrada de Audio (Speech-to-Text)**: Utiliza **Whisper** para transcribir la voz del usuario a texto.
* **Salida de Audio (Text-to-Speech)**: Utiliza **Edge-TTS** para sintetizar la respuesta del bot en audio (voz `es-AR-ElenaNeural`).
* **Panel de Administración**:
    * Inicio de sesión seguro (hardcodeado) para acceder a funciones técnicas.
    * Subida de nuevos documentos PDF.
    * Re-indexación de toda la base de conocimiento (PDFs + Wiki).
    * Exportación e importación del índice vectorial (ChromaDB).
* **Manejo de Versiones del Índice**: Cada indexación crea una nueva versión del índice y actualiza un puntero, permitiendo importaciones/exportaciones sin interrumpir el servicio.

## 🛠️ Stack Tecnológico

* **Backend**:
    * **Framework**: Flask
    * **RAG**: LangChain
    * **Vector Store**: ChromaDB
    * **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)
    * **Audio STT**: `openai-whisper`
    * **Audio TTS**: `edge-tts`
* **Frontend**:
    * **Framework**: React
    * **Estilos**: TailwindCSS
    * **Iconos**: `lucide-react`
* **Dependencia Clave (LLM)**:
    * **LM Studio**: La aplicación está diseñada para conectarse a un servidor local de LM Studio que sirva un modelo compatible (ej. `Meta-Llama-3-8B-Instruct`).

---

## 🔧 Instalación y Configuración

Sigue estos pasos para poner en marcha la aplicación.

### 1. Prerrequisitos

* **Python 3.10+**
* **Node.js 18+** (con `npm`)
* **LM Studio**: Debes tener LM Studio instalado y ejecutándose.
    * Descarga un modelo (ej. `Meta-Llama-3-8B-Instruct`).
    * Ve a la pestaña del servidor local (`<>`) y **ejecuta el servidor** en `http://localhost:1234`.

### 2. Clonar el Repositorio

```bash
git clone [https://github.com/tu-usuario/santiagooroz-equipo1-pp2-eldorado-2c-2025.git](https://github.com/tu-usuario/santiagooroz-equipo1-pp2-eldorado-2c-2025.git)
cd santiagooroz-equipo1-pp2-eldorado-2c-2025
````

### 3\. Configuración del Backend (Raíz)

1.  **Crear un entorno virtual** (recomendado):

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

2.  **Instalar dependencias de Python**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Rellenar credenciales de la wiki en el .env, opcional para integrar la wiki**:

    ```bash
    # Credenciales de la Wiki de El Dorado
    WIKI_BASE_URL="https://objetivos.eldoradosrl.ar/wiki"
    # Requerido para integrar la wiki. Rellenar credenciales
    WIKI_USERNAME="" 
    WIKI_PASSWORD=""
    ```

### 4\. Configuración del Frontend (`/frontend`)

1.  **Navegar a la carpeta del frontend**:

    ```bash
    cd frontend
    ```

2.  **Instalar dependencias de Node.js**:

    ```bash
    npm install
    ```

3.  **Regresar a la raíz**:

    ```bash
    cd ..
    ```

-----

## 🏃 Ejecución de la Aplicación

### 1\. ¡Inicia LM Studio\!

Asegúrate de que el servidor de LM Studio esté **activo** en `http://localhost:1234`.

### 2\. Indexación Inicial

Antes de iniciar la aplicación por primera vez, debes generar la base de datos vectorial.

Ejecuta el script de indexación manualmente:

```bash
python indexing.py
```

Esto leerá los archivos de `data/pdfs` y toda tu Wiki, generará los *embeddings* y los guardará en una nueva carpeta de versión en `data/` (ej. `data/chroma_db_v...`).

### 3\. Iniciar Backend y Frontend

Hemos incluido scripts para facilitar el inicio:

  * **En Windows**:
    ```bash
    iniciar_chatbot.bat
    ```
  * **En macOS/Linux**:
    ```bash
    chmod +x mac-linux-iniciar.command
    ./mac-linux-iniciar.command
    ```

Esto iniciará dos procesos:

1.  El servidor **Backend (Flask)** en `http://127.0.0.1:5000`.
2.  El servidor **Frontend (React)** en `http://localhost:3000` (y abrirá tu navegador).

-----

## ⚙️ Uso del Panel de Administración

Al abrir la aplicación (`http://localhost:3000`), se te presentará una pantalla de "Acceso Técnico".

  * **Contraseña**: `eldorado123`
    *(Nota: Se recomienda modificar la contraseña en `frontend/src/components/AppLayout.jsx`)*

Una vez dentro, el panel lateral (Sidebar) te permite gestionar la base de conocimiento:

  * **Seleccionar PDF**: Sube un nuevo archivo PDF a la carpeta `data/uploads`.
  * **📑 Indexar Conocimiento**: **Acción más importante.** Ejecuta el script `indexing.py` para re-escanear **todos** los PDFs (`data/pdfs` y `data/uploads`) y **toda** la Wiki. Crea un nuevo índice vectorial y lo activa.
  * **⬇️ Exportar Índice**: Descarga un archivo `.zip` de la base de datos ChromaDB activa.
  * **⬆️ Importar Índice**: Sube un archivo `.zip` (previamente exportado) para restaurar un índice.

-----

## 🗂 Estructura del Repositorio

A continuación, se detalla la función de los archivos clave en la raíz del proyecto.

```
└── santiagooroz-equipo1-pp2-eldorado-2c-2025/
    ├── app.py                    # Servidor principal de Flask: Define las APIs (/api/chat, /api/index, etc.) y maneja la lógica de RAG.
    ├── audio_utils.py            # Contiene las funciones para transcribir audio (Whisper) y sintetizar voz (Edge-TTS).
    ├── indexing.py               # Script para procesar PDFs y la Wiki, generar embeddings y crear el índice ChromaDB.
    ├── iniciar_chatbot.bat       # Script de inicio para Windows (inicia backend y frontend).
    ├── mac-linux-iniciar.command # Script de inicio para macOS/Linux (inicia backend y frontend).
    ├── metrics.py                # Módulo para la recolección de métricas de rendimiento y uso de la API.
    ├── requirements.txt          # Dependencias del backend de Python.
    ├── wiki_api.py               # Clase helper para conectarse, loguearse y extraer datos de la API de MediaWiki.
    └── frontend/                 # Contiene toda la aplicación de React.
        ├── README.md             # README original de Create React App.
        ├── package.json          # Dependencias y scripts del frontend (React, Tailwind).
        ├── postcss.config.js     # Configuración de PostCSS (para Tailwind).
        ├── tailwind.config.js    # Configuración de TailwindCSS (colores personalizados, etc.).
        ├── public/               # Archivos estáticos del frontend (HTML principal, íconos).
        └── src/                  # Código fuente de la aplicación React.
            ├── App.js            # Componente raíz de React.
            ├── index.js          # Punto de entrada de React.
            └── components/       # Componentes de la UI.
                ├── AppLayout.jsx # Estructura principal, maneja el login y la lógica del panel de admin.
                ├── Chat.jsx      # Componente de la interfaz de chat (mensajes, fuentes, audio).
                └── Sidebar.jsx   # Componente del panel lateral de administración.
```

-----

## 🧑‍💻 Desarrolladores

Este proyecto fue concebido y desarrollado por:

  * [Cristian Couto](https://www.linkedin.com/in/cristian-couto-147090211/)
  * [Santiago Oroz](https://www.linkedin.com/in/santiago-oroz/)
  * [Valeria Villegas](https://www.linkedin.com/in/valeria-s-villegas/)
  * [Stella Ventura](https://www.linkedin.com/in/stella-ventura)
  * [Belén Padrón](https://www.linkedin.com/in/mariana-bel%C3%A9n-padron-1199711b2/)

-----

## 🙏 Agradecimientos

  * A los profesores del **[Centro Politécnico Malvinas Argentinas](https://politecnico.ar/)** por su guía y apoyo invaluable durante el desarrollo de este proyecto.
  * A la empresa **El Dorado SRL** por brindarnos la oportunidad de colaborar y por facilitarnos los datos y documentos necesarios que forman la base de conocimiento de este asistente.

<!-- end list -->
