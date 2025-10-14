import os
import pickle
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
# Nota: La importación se hizo de langchain_community porque PyPDFLoader ya no está en el core de langchain
# pip install --upgrade langchain langchain-community

# --- CONFIGURACIÓN DE RUTAS ---
# 1. Rutas de entrada y salida
INPUT_DIR = Path("data/raw/Antecedentes PDF")
OUTPUT_DIR = Path("data/processed/objetospypdf")

# 2. Archivo a ignorar
EXCLUDE_FILE = ".gitkeep"


# --- PROCESO PRINCIPAL ---
def procesar_a_documentos_langchain():
    """
    Procesa todos los archivos PDF en INPUT_DIR, los convierte a objetos Document 
    de LangChain con metadatos y los guarda como archivos pickle.
    """
    print(f"Directorio de entrada: {INPUT_DIR.resolve()}")
    print(f"Directorio de salida: {OUTPUT_DIR.resolve()}")

    # 1. Crear el directorio de salida si no existe
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nDirectorio de salida creado o verificado: {OUTPUT_DIR.name}")
    except OSError as e:
        print(f"Error al crear el directorio de salida: {e}")
        return

    # 2. Verificar que el directorio de entrada exista
    if not INPUT_DIR.is_dir():
        print(f"Error: El directorio de entrada '{INPUT_DIR}' no existe o no es un directorio.")
        return

    # 3. Iterar sobre los archivos en el directorio de entrada
    for item_path in INPUT_DIR.iterdir():
        # Ignorar directorios, el archivo .gitkeep, y procesar solo archivos PDF
        if item_path.is_file() and item_path.suffix.lower() == '.pdf' and item_path.name != EXCLUDE_FILE:
            print(f"\n-> Procesando PDF: {item_path.name}")
            
            try:
                # Inicializar el cargador de LangChain
                loader = PyPDFLoader(str(item_path)) # Se convierte a str porque PyPDFLoader lo requiere
                
                # Cargar el documento. Esto divide automáticamente por página.
                documentos = loader.load()
                
                print(f"   Documentos generados: {len(documentos)} (Uno por página)")

                # 4. Mostrar una muestra de los metadatos
                if documentos:
                    doc_muestra = documentos[0]
                    print(f"   Metadatos del primer documento:")
                    # Muestra cómo LangChain añade automáticamente la fuente y la página.
                    print(f"     - source: {doc_muestra.metadata.get('source')}") 
                    print(f"     - page: {doc_muestra.metadata.get('page')}") 
                
                # 5. Guardar los documentos serializados (pickle)
                # Nombre de archivo de salida: T + nombre_original (sin extensión) + .pkl
                output_filename = "T" + item_path.stem + ".pkl"
                output_filepath = OUTPUT_DIR / output_filename
                
                with open(output_filepath, "wb") as f:
                    pickle.dump(documentos, f)
                
                print(f"   ✔️ Guardado exitosamente como objeto Python serializado (pickle): {output_filename}")

            except Exception as e:
                print(f"   ❌ Error al procesar el archivo {item_path.name}: {e}")

        elif item_path.name == EXCLUDE_FILE:
            print(f"-> Ignorando archivo: {EXCLUDE_FILE}")
        
        elif item_path.is_file() and item_path.suffix.lower() != '.pdf':
            print(f"-> Ignorando archivo no PDF: {item_path.name}")

    print("\n✅ Proceso de conversión a Documentos LangChain finalizado.")


# Ejecutar la función
if __name__ == "__main__":
    procesar_a_documentos_langchain()