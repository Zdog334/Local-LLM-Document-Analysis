# ingest.py

import os
import json
import faiss
import numpy as np
from pypdf import PdfReader
from models import embed
import unicodedata

DIM = 384
VECTOR_DIR = "vector_store"

os.makedirs(VECTOR_DIR, exist_ok=True)
os.makedirs("documents", exist_ok=True)


def get_storage_filename(original_filename: str) -> str:
    """
    Creates a filesystem-safe version of a filename.
    This is to prevent issues with libraries (like faiss) that may not
    handle special characters (e.g., accents) in paths correctly.
    It decomposes unicode characters and removes accents.
    Example: 'tílde.pdf' -> 'tilde.pdf'
    """
    # Normalize to NFD form to separate base characters from combining marks
    normalized = unicodedata.normalize('NFD', original_filename)
    # Remove combining marks (diacritics)
    storage_name = "".join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return storage_name

# -------------------------
# File Reader
# -------------------------

def read_file(path):
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    return open(path, encoding="utf-8", errors="ignore").read()


# -------------------------
# Chunking
# -------------------------

def chunk_text(text, chunk_size=800, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


# -------------------------
# Index Single File
# -------------------------

def ingest_file(path):

    if not os.path.isfile(path):
        return

    filename = os.path.basename(path)
    storage_filename = get_storage_filename(filename)

    print("Indexing:", filename)

    text = read_file(path)

    if not text.strip():
        print("⚠ Empty document:", filename)
        return

    file_chunks = chunk_text(text)

    if not file_chunks:
        print("⚠ No chunks generated for:", filename)
        return

    vectors = embed(file_chunks).astype("float32")

    index = faiss.IndexFlatL2(DIM)
    index.add(vectors)

    # Save per-file index
    index_path = os.path.join(VECTOR_DIR, f"{storage_filename}.index")
    json_path = os.path.join(VECTOR_DIR, f"{storage_filename}.json")

    faiss.write_index(index, index_path)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": file_chunks}, f, ensure_ascii=False, indent=2)

    print(f"✔ Indexed {filename} ({len(file_chunks)} chunks)")


# -------------------------
# Rebuild Everything
# -------------------------

def ingest_all_documents():

    print("Rebuilding all indexes...")

    # Optional: clear vector_store first
    for f in os.listdir(VECTOR_DIR):
        os.remove(os.path.join(VECTOR_DIR, f))

    for fname in os.listdir("documents"):
        path = os.path.join("documents", fname)

        if not os.path.isfile(path):
            continue

        ingest_file(path)

    print("✔ All documents indexed.")
