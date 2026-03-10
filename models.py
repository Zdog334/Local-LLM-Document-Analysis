# models.py
"""
Robust helper module for embeddings, token counting and Ollama generation.
This file uses lazy imports to avoid import-time failures and gives clear errors.
"""
import os
import requests

# --- CRITICAL: Set offline mode BEFORE importing transformers/sentence-transformers ---
def _check_and_set_offline_mode():
    """
    Checks for an internet connection. If unavailable, sets an environment
    variable to force Hugging Face Hub into offline mode. This must be done
    before importing the library to be effective.
    """
    try:
        # Try to connect to a reliable host with a short timeout
        requests.head("https://huggingface.co", timeout=2)
        print("✔ Internet connection detected.")
    except requests.exceptions.RequestException: # Catch all request-related errors
        print("⚠ No internet connection. Forcing Hugging Face Hub to offline mode.")
        os.environ["HF_HUB_OFFLINE"] = "1"

_check_and_set_offline_mode()

import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

_embedder = None  # global variable for the embedding model

# Define a persistent cache directory in the user's home folder
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".local_ai_studio_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = None
MAX_TOKENS = 25000

__all__ = ["embed", "generate", "trim_to_tokens", "count_tokens", "MAX_TOKENS"]


# ----- Tokenizer utilities (lazy tiktoken fallback) -----
@lru_cache(maxsize=1)
def _get_tokenizer():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        # fallback tokenizer: whitespace-based (coarse)
        return None


def count_tokens(text: str) -> int:
    enc = _get_tokenizer()
    if enc is None:
        # fallback: approximate by splitting on whitespace
        return max(1, len(text.split()))
    return len(enc.encode(text))


def trim_to_tokens(text: str, max_tokens: int = MAX_TOKENS) -> str:
    enc = _get_tokenizer()
    if enc is None:
        # fallback: approximate by characters (very rough)
        # assume 1 token ~ 4 chars, be conservative
        approx_chars = max_tokens * 3
        return text[-approx_chars:]
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    # keep last max_tokens tokens (context end)
    return enc.decode(tokens[-max_tokens:])


# ----- Embedding model (lazy load and cached) -----
@lru_cache(maxsize=1)
def _load_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "intfloat/multilingual-e5-small"
    print("Embedding device:", device)

    # 1. Try to load from cache first (offline-friendly)
    try:
        print(f"Attempting to load embedding model from local cache: {CACHE_DIR}")
        _embedder = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=CACHE_DIR,
            trust_remote_code=True,
            local_files_only=True
        )
        print("✔ Embedding model loaded from cache.")
        return _embedder
    except Exception:
        print(f"⚠ Local model not found in cache. Attempting to download...")

    # 2. If it fails, try to download (requires internet)
    try:
        _embedder = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=CACHE_DIR,
            trust_remote_code=True
        )
        print("✔ Embedding model downloaded and loaded.")
        return _embedder
    except Exception as e:
        raise ConnectionError(
            "Could not load embedding model. Please ensure you have an internet connection the first time you use this feature."
        ) from e

def embed(texts):
    model = _load_embedder()
    return model.encode(
        texts,
        batch_size=64,
        convert_to_numpy=True,
        show_progress_bar=False # Disabled for GUI
    )



# ----- Ollama generation (simple wrapper) -----
def generate(prompt: str, model: str = MODEL_NAME, timeout_seconds: int = 180) -> str:
    """
    Sends the prompt to Ollama's local API. Expects a JSON response containing "response".
    Raises clear errors if the server is unreachable or returns unexpected data.
    """
    if not model or model == "No models found":
        raise ValueError("No LLM model is selected. Please go to Settings and choose a model.")


    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout_seconds)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(
            f"Failed to connect to Ollama at {OLLAMA_URL}. Make sure Ollama is running and the model is loaded. "
            f"Original error: {e}"
        )
    
    if resp.status_code == 404:
        raise RuntimeError(f"Ollama couldn't find the model '{model}'")

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned status {resp.status_code}: {resp.text}")

    try:
        j = resp.json()
    except Exception:
        raise RuntimeError("Ollama response was not valid JSON: " + resp.text[:400])

    # adapt depending on the Ollama response shape
    if isinstance(j, dict) and "response" in j:
        return j["response"]
    # some Ollama setups include choices or output fields
    if "choices" in j and isinstance(j["choices"], list) and len(j["choices"]) > 0:
        # try common fields
        first = j["choices"][0]
        for key in ("text", "message", "content", "response"):
            if key in first:
                return first[key]
        # fallback: stringify first choice
        return str(first)
    # fallback: return JSON string
    return str(j)

class Document:
    def __init__(self, path, name):
        self.path = path
        self.name = name