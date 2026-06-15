"""Cross-encoder reranker for the RAG retrieval path.

Pull top-N from Qdrant via dense embeddings, then re-score the
(query, passage) pairs with `BAAI/bge-reranker-v2-m3` and return the
top-K by cross-encoder score.

This module is **additive** — it does not modify the Phase 1 dense
retrieval path. The CLI's `search` subcommand keeps the original
behaviour. Callers that want reranking import `Reranker` directly.
"""
from __future__ import annotations

import os
from typing import Any

from .config import HF_CACHE

# Route HF cache before importing transformers / sentence-transformers
os.environ.setdefault("HF_HOME", str(HF_CACHE))
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(HF_CACHE))

RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"


class Reranker:
    """Loads the cross-encoder once; rerank() is cheap per query."""

    def __init__(self) -> None:
        from sentence_transformers import CrossEncoder
        HF_CACHE.mkdir(parents=True, exist_ok=True)
        self._model = CrossEncoder(RERANKER_MODEL_NAME)

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 6,
        content_key: str = "content",
    ) -> list[dict[str, Any]]:
        """Sort `candidates` by cross-encoder relevance to `query`, return top_k.

        Each candidate must have `content_key` populated with the raw chunk
        text. The returned dicts gain a `rerank_score` field. The original
        cosine score, if present, is preserved untouched.
        """
        if not candidates:
            return []
        pairs = [(query, c[content_key]) for c in candidates]
        scores = self._model.predict(pairs, show_progress_bar=False)
        for c, s in zip(candidates, scores):
            c["rerank_score"] = float(s)
        return sorted(
            candidates, key=lambda c: c["rerank_score"], reverse=True
        )[:top_k]
