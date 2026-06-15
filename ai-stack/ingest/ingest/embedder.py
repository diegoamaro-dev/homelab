"""Sentence-transformers wrapper for multilingual-e5-small.

E5 family requires explicit prefixes:
  - "passage: " for documents you are storing
  - "query: "   for the user query at retrieval time

Forgetting the prefix silently degrades retrieval quality by ~10 points
in benchmarks, so we always add them in this module.
"""
from __future__ import annotations

import os
from typing import Iterable

from .config import EMBED_BATCH, EMBED_MODEL_NAME, HF_CACHE

# Route all HuggingFace caching to the shared openwebui cache. Must be set
# before sentence-transformers / huggingface_hub import.
os.environ.setdefault("HF_HOME", str(HF_CACHE))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(HF_CACHE))
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")  # 1st run downloads


class Embedder:
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        HF_CACHE.mkdir(parents=True, exist_ok=True)
        self._model = SentenceTransformer(EMBED_MODEL_NAME)

    def embed_passages(self, texts: Iterable[str]) -> list[list[float]]:
        prefixed = [f"passage: {t}" for t in texts]
        out = self._model.encode(
            prefixed, batch_size=EMBED_BATCH, normalize_embeddings=True,
            convert_to_numpy=False, show_progress_bar=False,
        )
        return [list(map(float, v)) for v in out]

    def embed_query(self, text: str) -> list[float]:
        v = self._model.encode(
            [f"query: {text}"], normalize_embeddings=True,
            convert_to_numpy=False, show_progress_bar=False,
        )[0]
        return list(map(float, v))
