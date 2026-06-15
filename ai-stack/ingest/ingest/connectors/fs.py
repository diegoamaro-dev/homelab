"""Filesystem connector.

Walks a corpus root, applies include/exclude globs, returns FileEntry per file.
"""
from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from ..config import Corpus


@dataclass
class FileEntry:
    source_path: str       # absolute
    source_rel: str        # relative to corpus root, POSIX separators
    source_kind: str
    text: str
    modified_at: str       # ISO 8601


def _match_one(rel_posix: str, pattern: str) -> bool:
    """fnmatch with a small extension: `**/X` also matches `X` at the root.

    Python's fnmatch has no recursive-glob semantics; `**` is just `**`. We
    add the conventional "match at any depth" interpretation by trying the
    pattern as-is *and* with the leading `**/` stripped.
    """
    if fnmatch.fnmatch(rel_posix, pattern):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatch(rel_posix, pattern[3:]):
        return True
    return False


def _matches_any(patterns: list[str], rel_posix: str) -> bool:
    return any(_match_one(rel_posix, p) for p in patterns)


def _classify(suffix: str, mapping: dict[str, str]) -> str | None:
    return mapping.get(suffix.lower())


def walk_files(corpus: Corpus) -> Iterator[FileEntry]:
    root = corpus.path.resolve()
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune common heavy dirs up front (faster than fnmatch on every file)
        dirnames[:] = [d for d in dirnames if d not in (
            ".git", "node_modules", "dist", "build",
            ".next", ".gradle", ".idea", ".venv", "venv", "__pycache__",
        )]
        for fn in filenames:
            abs_path = Path(dirpath) / fn
            try:
                rel = abs_path.relative_to(root).as_posix()
            except ValueError:
                continue

            if corpus.include and not _matches_any(corpus.include, rel):
                continue
            if corpus.exclude and _matches_any(corpus.exclude, rel):
                continue

            try:
                st = abs_path.stat()
            except OSError:
                continue
            if st.st_size > corpus.max_file_bytes:
                continue

            kind = _classify(abs_path.suffix, corpus.source_kind_map)
            if kind is None:
                continue

            try:
                text = abs_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            text = text.strip()
            if not text:
                continue

            yield FileEntry(
                source_path=str(abs_path),
                source_rel=rel,
                source_kind=kind,
                text=text,
                modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            )
