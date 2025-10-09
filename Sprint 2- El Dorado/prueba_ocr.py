
import pytesseract
from PIL import Image
import os

# Ruta exacta del ejecutable y de la carpeta de idiomas
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# Cargar la imagen (debe estar en la misma carpeta del script)
imagen = Image.open("texto_prueba.png")

# Ejecutar OCR (cambiar 'spa' por 'eng' si está en inglés)
texto = pytesseract.image_to_string(imagen, lang="spa")

# Mostrar el resultado
print("📄 Texto detectado:")
print(texto)
