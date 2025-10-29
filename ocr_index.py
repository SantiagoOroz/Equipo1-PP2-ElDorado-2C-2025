import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io, os, json

def extract_text_from_pdf(pdf_path):
    """Extrae texto de PDF; usa OCR si las páginas no tienen texto."""
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        text = page.get_text("text")
        if not text.strip():  # Si no hay texto, aplica OCR
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            text = pytesseract.image_to_string(img, lang="spa")
        full_text += text + "\n"

    return full_text.strip()

def process_pdfs(input_folder="data/pdfs", output_folder="data/ingested"):
    """Procesa todos los PDFs del directorio y los convierte a JSON."""
    # 🔹 Crea las carpetas si no existen (evita el FileNotFoundError)
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    data = []

    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            print(f"📄 Procesando: {file}")
            txt = extract_text_from_pdf(pdf_path)
            out_path = os.path.join(output_folder, file.replace(".pdf", ".json"))

            doc_data = {"file": file, "text": txt}
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)

            data.append(doc_data)

    if not data:
        print("⚠️ No se encontraron PDFs para procesar en:", input_folder)
    else:
        print(f"✅ Se procesaron {len(data)} documento(s).")

    return data
