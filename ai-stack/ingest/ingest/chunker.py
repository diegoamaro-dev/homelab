"""Text chunking.

Markdown files get header-aware splitting; everything else gets a plain
recursive character split. Both end up with ~CHUNK_SIZE-char windows with
CHUNK_OVERLAP characters of overlap.
"""
from __future__ import annotations

from .config import CHUNK_OVERLAP, CHUNK_SIZE


def _splitter(separators: list[str]):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=separators,
        keep_separator=False,
    )


def chunk_markdown(text: str) -> list[str]:
    """Header-aware markdown chunking. Falls back to recursive split."""
    from langchain_text_splitters import MarkdownHeaderTextSplitter

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=False,
    )
    try:
        sections = header_splitter.split_text(text)
    except Exception:
        sections = []

    body_splitter = _splitter(["\n\n", "\n", ". ", " ", ""])

    out: list[str] = []
    if sections:
        for doc in sections:
            body = doc.page_content
            if len(body) <= CHUNK_SIZE:
                out.append(body)
            else:
                out.extend(body_splitter.split_text(body))
    else:
        out = body_splitter.split_text(text)

    return [c.strip() for c in out if c and c.strip()]


def chunk_generic(text: str) -> list[str]:
    splitter = _splitter(["\n\n", "\n", " ", ""])
    return [c.strip() for c in splitter.split_text(text) if c and c.strip()]


def chunk(text: str, source_kind: str) -> list[str]:
    if source_kind == "markdown":
        return chunk_markdown(text)
    return chunk_generic(text)


def title_of(text: str, fallback: str) -> str:
    """Extract first markdown H1/H2, or fall back to the filename."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
        if s.startswith("## "):
            return s[3:].strip()
    return fallback
