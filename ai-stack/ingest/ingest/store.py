"""Qdrant wrapper.

We use deterministic point IDs derived from
sha256(collection|source_rel|chunk_index), formatted as a UUID. This makes
upserts idempotent and gives us cheap existence checks.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any, Iterable

from qdrant_client import QdrantClient, models as qm

from .config import EMBED_DIM, QDRANT_URL, qdrant_api_key


@dataclass
class Chunk:
    collection: str
    source_path: str
    source_rel: str
    source_kind: str
    chunk_index: int
    chunk_count: int
    content: str
    content_sha: str
    modified_at: str
    title: str
    vector: list[float] | None = None  # filled in by embedder


def point_id(collection: str, source_rel: str, chunk_index: int) -> str:
    """Deterministic UUIDv5-style id (string form) Qdrant accepts."""
    raw = f"{collection}|{source_rel}|{chunk_index}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def content_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Store:
    def __init__(self) -> None:
        self._client = QdrantClient(url=QDRANT_URL, api_key=qdrant_api_key(), timeout=30.0)

    # ---- read paths -------------------------------------------------

    def count(self, collection: str) -> int:
        return int(self._client.count(collection_name=collection, exact=True).count)

    def existing_content_shas_for(
        self, collection: str, source_rel: str
    ) -> dict[int, str]:
        """Return {chunk_index: content_sha} for every point matching source_rel."""
        flt = qm.Filter(must=[qm.FieldCondition(
            key="source_rel", match=qm.MatchValue(value=source_rel))])
        out: dict[int, str] = {}
        next_off = None
        while True:
            hits, next_off = self._client.scroll(
                collection_name=collection,
                scroll_filter=flt,
                with_payload=True,
                with_vectors=False,
                limit=256,
                offset=next_off,
            )
            for h in hits:
                p = h.payload or {}
                ci = p.get("chunk_index")
                cs = p.get("content_sha")
                if ci is not None and cs:
                    out[int(ci)] = cs
            if not next_off:
                break
        return out

    def all_source_rels(self, collection: str) -> set[str]:
        out: set[str] = set()
        next_off = None
        while True:
            hits, next_off = self._client.scroll(
                collection_name=collection,
                with_payload=["source_rel"],
                with_vectors=False,
                limit=512,
                offset=next_off,
            )
            for h in hits:
                p = h.payload or {}
                sr = p.get("source_rel")
                if sr:
                    out.add(sr)
            if not next_off:
                break
        return out

    # ---- write paths ------------------------------------------------

    def upsert_chunks(self, collection: str, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        points = [
            qm.PointStruct(
                id=point_id(c.collection, c.source_rel, c.chunk_index),
                vector=c.vector,
                payload={
                    "collection": c.collection,
                    "source_path": c.source_path,
                    "source_rel": c.source_rel,
                    "source_kind": c.source_kind,
                    "chunk_index": c.chunk_index,
                    "chunk_count": c.chunk_count,
                    "content": c.content,
                    "content_sha": c.content_sha,
                    "modified_at": c.modified_at,
                    "title": c.title,
                },
            )
            for c in chunks
        ]
        self._client.upsert(collection_name=collection, points=points, wait=True)
        return len(points)

    def delete_by_source_rel(self, collection: str, source_rels: Iterable[str]) -> int:
        rels = [r for r in source_rels]
        if not rels:
            return 0
        flt = qm.Filter(must=[qm.FieldCondition(
            key="source_rel", match=qm.MatchAny(any=rels))])
        before = self.count(collection)
        self._client.delete(collection_name=collection,
                            points_selector=qm.FilterSelector(filter=flt),
                            wait=True)
        after = self.count(collection)
        return before - after

    def delete_collection_data(self, collection: str) -> int:
        before = self.count(collection)
        self._client.delete(
            collection_name=collection,
            points_selector=qm.FilterSelector(filter=qm.Filter()),
            wait=True,
        )
        return before

    # ---- query ------------------------------------------------------

    def query(self, collection: str, vector: list[float], k: int = 6) -> list[dict[str, Any]]:
        res = self._client.query_points(
            collection_name=collection,
            query=vector,
            limit=k,
            with_payload=True,
        )
        out = []
        for p in res.points:
            payload = p.payload or {}
            out.append({
                "score": float(p.score),
                "source_rel": payload.get("source_rel"),
                "title": payload.get("title"),
                "chunk_index": payload.get("chunk_index"),
                "content": payload.get("content", "")[:400],
            })
        return out
