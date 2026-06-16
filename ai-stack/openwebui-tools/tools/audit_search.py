"""
title: Amarolab audit_search
author: amarolab
author_url: https://github.com/amaroou
description: Search the infra_audits corpus (past infrastructure audit reports and Phase 0/1 application logs) with dense retrieval + cross-encoder reranking. A schema-level shortcut over rag_search(collection="infra_audits", ...); use this whenever the user asks about audits, Phase 0/1 work, or the current state of a specific R-XX item.
version: 0.1.0
license: MIT
requirements:
"""

# @@AMAROLAB_INLINE:audit_helper@@

import json
import os
import sys
import time

from pydantic import BaseModel, Field


# The ingest tree is bind-mounted read-only into the openwebui
# container at /opt/ingest as of Phase B B-3 (2026-06-16). The Tool
# imports `Embedder` and `Reranker` from there at lazy-init time
# (see _init() below). Mirrors rag_search.py.
_INGEST_PATH = "/opt/ingest"
if _INGEST_PATH not in sys.path:
    sys.path.insert(0, _INGEST_PATH)


# Phase 1.5 + Phase B contract — locked. Same constants as
# rag_search.py (D-08). DENSE_N is intentionally a module constant,
# not a Valve; see rag_search.py and
# 09_logs/2026-06-17_phaseB_vc_validation.md §4.3 for the L-1
# escape hatch rationale.
DENSE_N = 30
TOP_K_DEFAULT = 6
TOP_K_MIN = 1
TOP_K_MAX = 12
QUERY_MIN_LEN = 2
QUERY_MAX_LEN = 500
CONTENT_CAP = 600

# Hardcoded per D-22 / 03-tools.md §"Tool 2 - audit_search". The
# whole point of this Tool existing as a separate schema entry is
# that the LLM's auto-routing is more reliable when the corpus
# choice is implicit in the tool name rather than passed as an arg.
_COLLECTION = "infra_audits"


class Tools:
    class Valves(BaseModel):
        max_per_minute: int = Field(
            default=30, ge=1, le=600,
            description="Per-process per-Tool rate limit (resets on openwebui restart). Same default as rag_search because audit_search shares the same heavy reranker pipeline.",
        )

    # Lazy runtime state. Class-level so it survives between
    # Tools() instantiations inside the same openwebui process.
    # Note: this Tool's _emb / _rer / _qdr are *independent* of
    # rag_search's class-level instances (each Tool runs in its
    # own tool_{id} module namespace per D-26). Cold-start cost
    # therefore pays ~5.6 s on the first audit_search call too,
    # even if rag_search has already warmed up.
    _emb = None
    _rer = None
    _qdr = None

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.citation = False

    def _init(self) -> None:
        if Tools._emb is None:
            # Heavy imports deferred to first call (matches rag_search.py).
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

    def audit_search(
        self,
        query: str,
        k: int = TOP_K_DEFAULT,
    ) -> str:
        """
        Search the Amarolab infrastructure audit corpus (past audit reports and Phase 0/1 application logs under /home/diego/server-audit-2026-06-13) with dense retrieval and cross-encoder reranking. Call this for questions about audits, sanitization, migration, what was applied in Phase 0/1, the current state of a specific R-XX remediation item, or the history of any infrastructure change recorded in the audit reports. Prefer this over rag_search when the question is about audits or past infra work; the collection is hardcoded so you do not need to pass it.

        :param query: Natural-language question or topic, 2-500 characters. Spanish or English both supported.
        :param k: How many reranked hits to return (1-12, default 6).
        :return: JSON string with keys collection ("infra_audits"), query, hits[]. Each hit has rank, source_rel, title, chunk_index, score, content (truncated to 600 chars). On error: {"error": "...", "code": "..."}. On empty result: {"hits": [], "code": "empty_collection"}.
        """
        t0 = time.monotonic()
        args_snap = {"query": query, "k": k}

        # Input validation. `query` and `k` are the only caller-supplied
        # parameters; collection is hardcoded so there is no bad_collection
        # path. Same shape as rag_search.py for grep parity in the audit log.
        if not isinstance(query, str) or len(query) < QUERY_MIN_LEN or len(query) > QUERY_MAX_LEN:
            _audit("audit_search", args_snap, allowed=False, result_code="bad_query")
            return json.dumps({
                "error": f"query must be {QUERY_MIN_LEN}-{QUERY_MAX_LEN} characters",
                "code": "bad_query",
            })
        if not isinstance(k, int) or k < TOP_K_MIN or k > TOP_K_MAX:
            _audit("audit_search", args_snap, allowed=False, result_code="bad_k")
            return json.dumps({
                "error": f"k must be an integer between {TOP_K_MIN} and {TOP_K_MAX}",
                "code": "bad_k",
            })

        if not _RateLimiter.check("audit_search", self.valves.max_per_minute):
            _audit("audit_search", args_snap, allowed=False, result_code="rate_limited")
            return json.dumps({
                "error": "rate limit exceeded",
                "code": "rate_limited",
            })

        try:
            self._init()
        except Exception as e:
            _audit("audit_search", args_snap, allowed=False, result_code="init_error",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "error": "runtime initialisation failed",
                "code": "init_error",
                "detail": f"{e.__class__.__name__}: {e}",
            })

        try:
            vec = Tools._emb.embed_query(query)
            res = Tools._qdr.query_points(
                collection_name=_COLLECTION,
                query=vec,
                limit=DENSE_N,
                with_payload=True,
            )
        except Exception as e:
            _audit("audit_search", args_snap, allowed=False, result_code="qdrant_unreachable",
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
            # Defensive — infra_audits has 280 chunks as of Phase B B-2,
            # so 0 hits would mean Qdrant returned empty (unlikely) or
            # the collection got wiped. Same shape as rag_search.py
            # so the LLM's empty-collection refusal phrasing is identical.
            _audit("audit_search", args_snap, result_code="empty_collection",
                   duration_ms=int((time.monotonic() - t0) * 1000))
            return json.dumps({
                "collection": _COLLECTION,
                "query": query,
                "hits": [],
                "code": "empty_collection",
            })

        try:
            top = Tools._rer.rerank(query, cands, top_k=k)
        except Exception as e:
            _audit("audit_search", args_snap, allowed=False, result_code="rerank_error",
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

        _audit("audit_search", args_snap, result_code="ok",
               duration_ms=int((time.monotonic() - t0) * 1000))
        return json.dumps({
            "collection": _COLLECTION,
            "query": query,
            "hits": hits,
        }, ensure_ascii=False)
