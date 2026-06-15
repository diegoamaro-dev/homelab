"""Corpus + runtime configuration.

The .env file beside the ai-stack tree holds the secrets; here we just read it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Filesystem layout
INGEST_ROOT = Path("/home/diego/homelab/ai-stack/ingest")
CORPORA_YAML = INGEST_ROOT / "conf" / "corpora.yaml"
LOG_DIR = INGEST_ROOT / "logs"

# Embedding model
EMBED_MODEL_NAME = "intfloat/multilingual-e5-small"
EMBED_DIM = 384
EMBED_BATCH = 32

# Chunking
CHUNK_SIZE = 600          # characters (~ tokens for English/Spanish)
CHUNK_OVERLAP = 80

# Qdrant
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")

# Shared HuggingFace cache (already populated by openwebui)
HF_CACHE = Path("/srv/homelab/data/openwebui/cache/embedding/models")


def load_env_file(env_path: Path = Path("/home/diego/homelab/ai-stack/.env")) -> None:
    """Load KEY=VALUE pairs from the .env file into os.environ if not already set."""
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and v and k not in os.environ:
            os.environ[k] = v


@dataclass
class Corpus:
    name: str
    type: str                          # 'fs' or 'git'
    path: Path
    include: list[str]
    exclude: list[str]
    enabled: bool
    source_kind_map: dict[str, str]
    max_file_bytes: int


@dataclass
class IngestConfig:
    corpora: list[Corpus]
    defaults: dict[str, Any] = field(default_factory=dict)


def load_corpora(yaml_path: Path = CORPORA_YAML) -> IngestConfig:
    raw = yaml.safe_load(yaml_path.read_text())
    defaults = raw.get("defaults", {}) or {}
    source_kind_map = defaults.get("source_kind_map", {}) or {}
    exclude_global = defaults.get("exclude_global", []) or []
    max_file_bytes = int(defaults.get("max_file_bytes", 5_000_000))

    corpora: list[Corpus] = []
    for entry in raw.get("corpora", []):
        excludes = list(entry.get("exclude", []) or []) + list(exclude_global)
        corpora.append(
            Corpus(
                name=entry["name"],
                type=entry["type"],
                path=Path(entry["path"]),
                include=list(entry.get("include", []) or []),
                exclude=excludes,
                enabled=bool(entry.get("enabled", True)),
                source_kind_map=dict(source_kind_map),
                max_file_bytes=max_file_bytes,
            )
        )
    return IngestConfig(corpora=corpora, defaults=defaults)


def qdrant_api_key() -> str:
    load_env_file()
    key = os.environ.get("QDRANT_API_KEY") or os.environ.get("QDRANT__SERVICE__API_KEY")
    if not key:
        raise RuntimeError(
            "QDRANT_API_KEY not found in env or "
            "/home/diego/homelab/ai-stack/.env"
        )
    return key
