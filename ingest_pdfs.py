import json, os
from ocr_index import process_pdfs

INDEX_PATH = "data/ingested/index.json"

def build_index():
    docs = process_pdfs()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"✅ Índice actualizado con {len(docs)} documentos.")

if __name__ == "__main__":
    build_index()
