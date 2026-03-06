import os
import json
import faiss
import numpy as np
from models import embed, generate

VECTOR_DIR = "vector_store"

# global configuration
CURRENT_LANGUAGE = None

def set_language(lang):
    """Set the language that future responses should be forced into.
    Pass None or empty string to clear the override.
    """
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = lang if lang else None


def load_file_index(filename):
    index_path = os.path.join(VECTOR_DIR, f"{filename}.index")
    store_path = os.path.join(VECTOR_DIR, f"{filename}.json")

    if not os.path.exists(index_path) or not os.path.exists(store_path):
        return None, None

    index = faiss.read_index(index_path)
    chunks = json.load(open(store_path, "r", encoding="utf-8"))["chunks"]

    return index, chunks


def query_knowledge(query, selected_files, k=6):

    if not selected_files:
        return "No files selected.", []

    q_vec = embed([query])[0]

    all_results = []

    # Search each selected file independently
    for filename in selected_files:

        index, chunks = load_file_index(filename)

        if index is None or not chunks:
            continue

        D, I = index.search(np.array([q_vec]), k)

        for score, idx in zip(D[0], I[0]):
            if idx < len(chunks):
                all_results.append({
                    "file": filename,
                    "content": chunks[idx],
                    "score": float(score)
                })

    if not all_results:
        return "No relevant passages found.", []

    # Sort globally by similarity
    all_results.sort(key=lambda x: x["score"])

    # Keep top k total
    top_results = all_results[:k]

    context = "\n\n---\n\n".join(
        f"[{r['file']}]\n{r['content']}"
        for r in top_results
    )

    # build the prompt with optional language override
    prompt = """
You are a research assistant.

Use ONLY the context below to answer.
If the answer is not contained, say so.
If multiple documents are provided, compare and contrast them if relevant.
Indicate which document(s) each part of the answer is based on, using [[filename.pdf]] notation.
"""

    # force language if set
    if CURRENT_LANGUAGE:
        prompt = f"Answer in {CURRENT_LANGUAGE}.\n\n" + prompt

    prompt += f"\nContext:\n{context}\n\nQuestion: {query}\n"

    answer = generate(prompt)

    return answer, top_results
