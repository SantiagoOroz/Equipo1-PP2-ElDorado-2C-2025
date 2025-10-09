
import pytesseract
from PIL import Image
import os

# 🔧 Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# 📷 Cargar la imagen (asegurate que el nombre sea correcto)
imagen = Image.open("imagen_prueba.png")

# 🧠 Ejecutar OCR
texto = pytesseract.image_to_string(imagen, lang="spa")

# 💾 Guardar el texto en un archivo .txt
with open("texto_extraido_imagen.txt", "w", encoding="utf-8") as archivo:
    archivo.write(texto)

# ✅ Confirmar en la consola
print("📄 Texto detectado:")
print(texto)
print("\n✅ El texto se guardó en 'texto_extraido_imagen.txt'")
