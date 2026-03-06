import faiss, json, requests
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("intfloat/multilingual-e5-small")
index = faiss.read_index("vector_store/index.bin")
texts = json.load(open("vector_store/texts.json"))

def ask(query):
    qvec = embedder.encode([query])
    D,I = index.search(qvec, 5)

    context = "\n".join([texts[i] for i in I[0]])

    prompt = f"""
Use the following context to answer.
If unsure, say so.

Context:
{context}

Question:
{query}
"""

    r = requests.post("http://localhost:11434/api/generate", json={
        "model":"qwen2.5:1.5b",
        "prompt":prompt,
        "stream":False
    })
    return r.json()["response"], context
