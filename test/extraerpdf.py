from pypdf import PdfReader
import os
from pathlib import Path

# --- CONFIGURACIÓN DE RUTAS ---
# 1. Rutas de entrada y salida
INPUT_DIR = Path("data/raw/Antecedentes PDF")
OUTPUT_DIR = Path("data/processed/extraidosconpypdf")

# 2. Archivo a ignorar
EXCLUDE_FILE = ".gitkeep"

# --- FUNCIÓN PRINCIPAL DE EXTRACCIÓN ---
def extraer_texto_de_pdf(pdf_path: Path) -> str:
    """Extrae el texto completo de un archivo PDF dado."""
    texto_completo = ""
    try:
        reader = PdfReader(pdf_path)
        
        # Iterar sobre cada página
        for i, page in enumerate(reader.pages):
            texto_de_pagina = page.extract_text()
            if texto_de_pagina:
                # Añade el texto de la página y un separador
                texto_completo += texto_de_pagina + "\n\n--- FIN DE PÁGINA ---\n\n"
            else:
                # Marca las páginas no reconocibles
                texto_completo += f"\n\n--- PÁGINA {i+1} VACÍA O NO RECONOCIBLE ---\n\n"
        
        return texto_completo

    except Exception as e:
        print(f"Error al procesar el archivo {pdf_path.name}: {e}")
        return f"*** ERROR DE PROCESAMIENTO: {e} ***"


# --- PROCESO PRINCIPAL ---
def procesar_todos_los_pdfs():
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
    for item in INPUT_DIR.iterdir():
        # Ignorar directorios, el archivo .gitkeep, y procesar solo archivos PDF
        if item.is_file() and item.suffix.lower() == '.pdf' and item.name != EXCLUDE_FILE:
            print(f"\n-> Procesando: {item.name}")
            
            # 4. Extraer el texto
            texto_extraido = extraer_texto_de_pdf(item)
            
            # 5. Generar el nombre y la ruta del archivo de salida
            # Nombre de archivo de salida: T + nombre_original (sin extensión) + .txt
            output_filename = "T" + item.stem + ".txt"
            output_filepath = OUTPUT_DIR / output_filename
            
            # 6. Guardar el texto extraído
            try:
                with open(output_filepath, "w", encoding="utf-8") as f:
                    f.write(texto_extraido)
                print(f"   ✔️ Guardado exitosamente como: {output_filename}")
            except Exception as e:
                print(f"   ❌ Error al guardar el archivo de salida {output_filename}: {e}")

        elif item.name == EXCLUDE_FILE:
            print(f"-> Ignorando archivo: {EXCLUDE_FILE}")
        
        elif item.is_file() and item.suffix.lower() != '.pdf':
            print(f"-> Ignorando archivo no PDF: {item.name}")

    print("\n✅ Proceso de transcripción masiva finalizado.")


# Ejecutar la función
if __name__ == "__main__":
    procesar_todos_los_pdfs()