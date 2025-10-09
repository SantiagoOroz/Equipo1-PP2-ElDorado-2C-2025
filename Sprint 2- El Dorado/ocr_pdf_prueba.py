
import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# 🔧 Rutas exactas de Tesseract y carpeta tessdata
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

print("🔍 Ejecutando OCR del PDF...")

# Cambiá el nombre si tu PDF se llama distinto
paginas = convert_from_path("documento_prueba.pdf")

for i, pagina in enumerate(paginas):
    print(f"📄 Leyendo página {i+1}...")
    texto = pytesseract.image_to_string(pagina, lang="spa")
    print("📝 Texto detectado:")
    print(texto)
