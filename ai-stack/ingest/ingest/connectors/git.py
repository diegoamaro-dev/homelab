"""Git connector.

For git-backed corpora we (optionally) try a fast-forward pull before walking.
A dirty working tree skips the pull instead of failing — local edits win.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import Corpus
from .fs import FileEntry, walk_files


def _try_git_pull(repo: Path) -> tuple[bool, str]:
    if not (repo / ".git").exists():
        return False, "not a git repo"
    try:
        dirty = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
    except subprocess.SubprocessError as e:
        return False, f"git status failed: {e}"
    if dirty:
        return False, f"dirty working tree, skipped pull ({len(dirty.splitlines())} files)"
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "pull", "--ff-only"],
            capture_output=True, text=True, check=True, timeout=30,
        )
    except subprocess.SubprocessError as e:
        return False, f"git pull failed: {e}"
    return True, out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "up to date"


def pull_then_walk(corpus: Corpus, *, pull: bool = True):
    """Yield (info_str_once, file_entries…). info_str is a one-line summary."""
    ok, info = (False, "skipped")
    if pull:
        ok, info = _try_git_pull(corpus.path)
    yield ("git", f"{corpus.name}: {info}")
    yield from (("file", fe) for fe in walk_files(corpus))
