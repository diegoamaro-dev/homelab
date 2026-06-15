"""End-to-end ingestion pipeline.

For each corpus:
  1. (optional) git pull
  2. walk files
  3. chunk each file
  4. compare chunk content_sha to what's already in Qdrant
  5. embed + upsert the changed/new chunks
  6. delete points for files that no longer exist on disk
  7. return a run report
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .chunker import chunk as chunk_text
from .chunker import title_of
from .config import Corpus
from .connectors.fs import FileEntry, walk_files
from .connectors.git import pull_then_walk
from .embedder import Embedder
from .store import Chunk, Store, content_sha


@dataclass
class CorpusReport:
    name: str
    git_info: str = ""
    files_seen: int = 0
    files_skipped_unchanged: int = 0
    files_with_changes: int = 0
    chunks_upserted: int = 0
    chunks_unchanged: int = 0
    files_deleted: int = 0
    points_deleted: int = 0
    errors: list[str] = field(default_factory=list)


def _iter_files(corpus: Corpus):
    if corpus.type == "git":
        for kind, payload in pull_then_walk(corpus):
            if kind == "git":
                yield ("git_info", payload)
            else:
                yield ("file", payload)
    else:
        for fe in walk_files(corpus):
            yield ("file", fe)


def _file_chunks(fe: FileEntry, corpus_name: str) -> list[Chunk]:
    raw = chunk_text(fe.text, fe.source_kind)
    if not raw:
        return []
    title = title_of(fe.text, Path(fe.source_rel).name)
    n = len(raw)
    return [
        Chunk(
            collection=corpus_name,
            source_path=fe.source_path,
            source_rel=fe.source_rel,
            source_kind=fe.source_kind,
            chunk_index=i,
            chunk_count=n,
            content=text,
            content_sha=content_sha(text),
            modified_at=fe.modified_at,
            title=title,
        )
        for i, text in enumerate(raw)
    ]


def sync_corpus(corpus: Corpus, embedder: Embedder, store: Store, *, dry_run: bool = False) -> CorpusReport:
    rep = CorpusReport(name=corpus.name)
    if not corpus.enabled:
        rep.errors.append("corpus disabled in corpora.yaml — skipped")
        return rep
    if not corpus.path.exists():
        rep.errors.append(f"path does not exist: {corpus.path}")
        return rep

    seen_rels: set[str] = set()
    pending_chunks: list[Chunk] = []   # waiting for embedding

    for kind, payload in _iter_files(corpus):
        if kind == "git_info":
            rep.git_info = str(payload)
            continue
        fe: FileEntry = payload
        rep.files_seen += 1
        seen_rels.add(fe.source_rel)

        new_chunks = _file_chunks(fe, corpus.name)
        if not new_chunks:
            continue

        existing = store.existing_content_shas_for(corpus.name, fe.source_rel)
        unchanged_in_file = 0
        chunks_to_embed: list[Chunk] = []
        new_count = len(new_chunks)

        for c in new_chunks:
            if existing.get(c.chunk_index) == c.content_sha:
                unchanged_in_file += 1
            else:
                chunks_to_embed.append(c)

        # If the file shrank, delete the orphan chunk_indexes
        orphan_indexes = [i for i in existing.keys() if i >= new_count]
        if orphan_indexes and not dry_run:
            # We don't have a direct "delete by source_rel + chunk_index" helper;
            # for files that shrank we just drop the whole file's points and
            # re-embed all chunks for simplicity.
            store.delete_by_source_rel(corpus.name, [fe.source_rel])
            chunks_to_embed = new_chunks
            unchanged_in_file = 0

        rep.chunks_unchanged += unchanged_in_file
        if chunks_to_embed:
            rep.files_with_changes += 1
            pending_chunks.extend(chunks_to_embed)
        else:
            rep.files_skipped_unchanged += 1

    # Batch-embed and upsert in groups of EMBED_BATCH×4 to limit RAM
    if pending_chunks and not dry_run:
        FLUSH = 128
        for i in range(0, len(pending_chunks), FLUSH):
            batch = pending_chunks[i : i + FLUSH]
            vecs = embedder.embed_passages([c.content for c in batch])
            for c, v in zip(batch, vecs):
                c.vector = v
            rep.chunks_upserted += store.upsert_chunks(corpus.name, batch)

    # Garbage-collect points whose file is no longer present
    stored_rels = store.all_source_rels(corpus.name)
    gone = sorted(stored_rels - seen_rels)
    if gone and not dry_run:
        deleted = store.delete_by_source_rel(corpus.name, gone)
        rep.files_deleted = len(gone)
        rep.points_deleted = deleted
    elif gone:
        rep.files_deleted = len(gone)

    return rep
