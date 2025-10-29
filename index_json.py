# ingest_pdfs.py
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
import json, os

# Directorios
PDF_DIR = "data/pdfs"
OUTPUT_DIR = "data/json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def pdf_to_text(pdf_path):
    """Convierte un PDF a texto utilizando OCR."""
    text = ""
    images = convert_from_path(pdf_path)
    for img in images:
        text += pytesseract.image_to_string(img, lang="spa") + "\n"
    return text.strip()

def ingest_pdfs():
    """Procesa todos los PDFs del directorio y los guarda como JSON."""
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            path = os.path.join(PDF_DIR, filename)
            print(f"Procesando {filename}...")
            text = pdf_to_text(path)

            data = {"filename": filename, "text": text}
            json_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ Archivo convertido: {json_path}")

if __name__ == "__main__":
    ingest_pdfs()
