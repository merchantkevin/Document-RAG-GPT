"""Minimal in-memory vector store backed by FAISS (cosine via inner product)."""
from typing import List, Dict
import faiss
import numpy as np


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.metadatas: List[Dict] = []  # parallel to vectors: {"text", "source"}

    def add(self, embeddings: np.ndarray, metadatas: List[Dict]) -> None:
        self.index.add(embeddings)
        self.metadatas.extend(metadatas)

    def search(self, query_embedding: np.ndarray, k: int = 4) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        scores, idxs = self.index.search(query_embedding, k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            md = self.metadatas[idx]
            results.append({"text": md["text"], "source": md["source"], "score": float(score)})
        return results

    def __len__(self) -> int:
        return self.index.ntotal
