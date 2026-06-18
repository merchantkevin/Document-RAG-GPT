"""Sentence-Transformers embedding wrapper (loaded once, thread-safe)."""
import os
import threading
from typing import List
import numpy as np

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBED_DIM = 384  # all-MiniLM-L6-v2 output dimension

_model = None
_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts: List[str]) -> np.ndarray:
    """Return L2-normalized float32 embeddings (so inner product == cosine)."""
    model = get_model()
    emb = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return emb.astype("float32")
