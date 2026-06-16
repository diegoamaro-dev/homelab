"""
title: Amarolab rag_search
author: amarolab
author_url: https://github.com/amaroou
description: Search an Amarolab knowledge corpus (homelab_docs, guardian_cloud, ensambla2, infra_audits, or myfreetour) with dense retrieval + cross-encoder reranking and return the top-k reranked chunks with source citations.
version: 0.1.0
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@

import json
import os
import sys
import time
from typing import Literal

from pydantic import BaseModel, Field


# The ingest tree is bind-mounted read-only into the openwebui
# container at /opt/ingest as of Phase B B-3 (2026-06-16). The Tool
# imports `Embedder` and `Reranker` from there at lazy-init time
# (see _init() below). This sys.path insert is cheap and happens
# at module load; the heavy sentence-transformers imports stay
# deferred to the first call.
_INGEST_PATH = "/opt/ingest"
if _INGEST_PATH not in sys.path:
    sys.path.insert(0, _INGEST_PATH)


# Phase 1.5 + Phase B contract — locked.
# DENSE_N is intentionally a module constant, not a Valve. V-C
# validation 2026-06-17 confirmed DENSE_N=30 reproduces the Phase
# 1.5 reranker benchmark with 0 pp drift on top-1/3/6.
# L-1 escape hatch: if per-call rerank latency (~10 s at DENSE_N=30
# on this hardware) ever becomes a UX complaint after B-8, lower
# this toward ~12 and re-run the 20-question fixture before
# relocking. See 09_logs/2026-06-17_phaseB_vc_validation.md §4.3.
DENSE_N = 30
TOP_K_DEFAULT = 6
TOP_K_MIN = 1
TOP_K_MAX = 12
QUERY_MIN_LEN = 2
QUERY_MAX_LEN = 500
CONTENT_CAP = 600  # max chars of chunk content per returned hit; matches the ingest CHUNK_SIZE target


class Tools:
    class Valves(BaseModel):
        max_per_minute: int = Field(
            default=30, ge=1, le=600,
            description="Per-process per-Tool rate limit (resets on openwebui restart). Lower than time_now because each call runs the bge-reranker-v2-m3 cross-encoder over 30 candidate chunks.",
        )

    # Lazy runtime state. Class-level (not instance-level) so it
    # survives between Tools() instantiations inside the same
    # openwebui process. First rag_search call pays ~5.6 s of
    # cold model load (embedder 4.19 s + reranker 1.35 s, per V-C
    # measurement); subsequent calls reuse the loaded models.
    _emb = None
    _rer = None
    _qdr = None

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def _init(self) -> None:
        if Tools._emb is None:
            # Heavy imports are deferred to first call so module
            # load (and Open WebUI's tool spec build) stays cheap.
            from ingest.embedder import Embedder
            from ingest.reranker import Reranker
            from qdrant_client import QdrantClient

            url = os.environ.get("QDRANT_URI") or os.environ.get("QDRANT_URL")
            if not url:
                raise RuntimeError("Qdrant URL not set: QDRANT_URI / QDRANT_URL missing from container env")
            key = (
                os.environ.get("QDRANT_API_KEY")
                or os.environ.get("QDRANT__SERVICE__API_KEY")
            )
            if not key:
                raise RuntimeError("Qdrant API key not set: QDRANT_API_KEY / QDRANT__SERVICE__API_KEY missing from container env")

            Tools._emb = Embedder()
            Tools._rer = Reranker()
            Tools._qdr = QdrantClient(url=url, api_key=key, timeout=30.0)

    def rag_search(
        self,
        collection: Literal[
            "homelab_docs",
            "guardian_cloud",
            "ensambla2",
            "infra_audits",
            "myfreetour",
        ],
        query: str,
        k: int = TOP_K_DEFAULT,
    ) -> str:
        """
        Search an Amarolab knowledge corpus and return reranked top-k chunks with source citations. Call this whenever the user asks something that requires grounding in documentation: homelab infrastructure, Guardian Cloud product/architecture/recovery, Ensambla2 product/auth/multitenancy, past infrastructure audits, or MyFreeTour (placeholder, returns empty_collection). Pick the most specific collection; do not guess across collections. Use audit_search for audit/Phase 0 questions when it is available.

        :param collection: One of "homelab_docs" (homelab infrastructure docs), "guardian_cloud" (Guardian Cloud product docs - read only), "ensambla2" (Ensambla2 product docs), "infra_audits" (past infra audit reports and Phase 0/1 application logs), "myfreetour" (placeholder - returns empty_collection until corpus is indexed).
        :param query: Natural-language question or topic, 2-500 characters. Spanish or English both supported.
        :param k: How many reranked hits to return (1-12, default 6).
        :return: JSON string with keys collection, query, hits[]. Each hit has rank, source_rel, title, chunk_index, score, content (truncated to 600 chars). On error or empty collection: {"error": "...", "code": "..."} or {"hits": [], "code": "empty_collection"}.
        """
        t0 = time.monotonic()
        args_snap = {"collection": collection, "query": query, "k": k}

        # Input validation. Literal[…] already constrains `collection`;
        # we still validate query/k explicitly so a misbehaving caller
        # gets a structured error instead of a 500 from Qdrant.
        if not isinstance(query, str) or len(query) < QUERY_MIN_LEN or len(query) > QUERY_MAX_LEN:
            _audit("rag_search", args_snap, allowed=False, result_code="bad_query")
            return json.dumps({
                "error": f"query must be {QUERY_MIN_LEN}-{QUERY_MAX_LEN} characters",
                "code": "bad_query",
            })
        if not isinstance(k, int) or k < TOP_K_MIN or k > TOP_K_MAX:
            _audit("rag_search", args_snap, allowed=False, result_code="bad_k")
            return json.dumps({
                "error": f"k must be an integer between {TOP_K_MIN} and {TOP_K_MAX}",
                "code": "bad_k",
            })

        if not _RateLimiter.check("rag_search", self.valves.max_per_minute):
            _audit("rag_search", args_snap, allowed=False, result_code="rate_limited")
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        try:
            self._init()
        except Exception as e:
            _audit("rag_search", args_snap, allowed=False, result_code="init_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "runtime initialisation failed",
                "code": "init_error",
                "detail": f"{e.__class__.__name__}: {e}",
            })

        try:
            vec = Tools._emb.embed_query(query)
            res = Tools._qdr.query_points(
                collection_name=collection,
                query=vec,
                limit=DENSE_N,
                with_payload=True,
            )
        except Exception as e:
            _audit("rag_search", args_snap, allowed=False, result_code="qdrant_unreachable",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "could not reach the knowledge base",
                "code": "qdrant_unreachable",
                "detail": e.__class__.__name__,
            })

        cands = []
        for p in res.points:
            payload = p.payload or {}
            cands.append({
                "source_rel": payload.get("source_rel"),
                "title": payload.get("title"),
                "chunk_index": payload.get("chunk_index"),
                "content": payload.get("content", ""),
                "cosine_score": float(p.score),
            })

        if not cands:
            # D-22: myfreetour is the documented placeholder; any
            # other corpus also reports empty_collection if Qdrant
            # returns 0 hits, so the LLM apologises cleanly instead
            # of silently picking another corpus.
            _audit("rag_search", args_snap, result_code="empty_collection",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "collection": collection,
                "query": query,
                "hits": [],
                "code": "empty_collection",
            })

        try:
            top = Tools._rer.rerank(query, cands, top_k=k)
        except Exception as e:
            _audit("rag_search", args_snap, allowed=False, result_code="rerank_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "rerank pass failed",
                "code": "rerank_error",
                "detail": e.__class__.__name__,
            })

        hits = []
        for i, h in enumerate(top):
            content = h.get("content") or ""
            if len(content) > CONTENT_CAP:
                content = content[:CONTENT_CAP]
            hits.append({
                "rank": i + 1,
                "source_rel": h.get("source_rel"),
                "title": h.get("title"),
                "chunk_index": h.get("chunk_index"),
                "score": round(float(h.get("rerank_score", 0.0)), 4),
                "content": content,
            })

        _audit("rag_search", args_snap, result_code="ok",
               duration_ms=int((time.monotonic() - t0) * 1000))
        return json.dumps({
            "collection": collection,
            "query": query,
            "hits": hits,
        }, ensure_ascii=False)
