"""
cli.py — orchestrate Parse → Resolve → Normalize → Validate → Emit.

    python3 -m _loader.cli               # build + emit world_model.generated.json
    python3 -m _loader.cli --check       # validate only (no emit)
    python3 -m _loader.cli --reproducible# fixed timestamp (determinism gate)

Fail-loud: on validation failure the loader prints all problems, writes nothing,
and exits non-zero — the previous artifact (last-good) is retained untouched.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import emit, normalize, parse, registry, resolve, validate

ROOT = Path(__file__).resolve().parent.parent            # …/world_model
SCHEMA_DIR = ROOT / "_schema"
DEFAULT_ARTIFACT = ROOT / "world_model.generated.json"


def _docs_commit() -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except Exception:
        return None


def compile_model(root: Path = ROOT):
    """Parse → Resolve → Normalize → Validate. Returns (entities, reg). Raises on invalid."""
    reg = registry.load(root / "_schema")
    entities, archetypes = parse.parse_tree(root)
    entities = resolve.resolve(entities, archetypes, reg)
    entities = normalize.normalize(entities, reg)
    validate.validate(entities, archetypes, reg)
    return entities, reg


def build_artifact(root: Path = ROOT, reproducible: bool = False) -> dict:
    entities, reg = compile_model(root)
    generated_at = ("1970-01-01T00:00:00Z" if reproducible
                    else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    return emit.build(entities, reg, docs_commit=_docs_commit(), generated_at=generated_at)


def run(check_only: bool = False, reproducible: bool = False,
        emit_to: Path | None = None, root: Path = ROOT) -> int:
    emit_to = emit_to or (root / "world_model.generated.json")
    try:
        artifact = build_artifact(root, reproducible=reproducible)
    except validate.ValidationError as exc:
        print(f"world-model loader: VALIDATION FAILED — {exc}", file=sys.stderr)
        print("world-model loader: no artifact written; last-good retained.", file=sys.stderr)
        return 2

    if check_only:
        print(f"world-model loader: OK (check-only) — {artifact['stats']}", file=sys.stderr)
        return 0

    emit.write_atomic(emit_to, emit.serialize(artifact))
    print(f"world-model loader: OK — wrote {emit_to.name} ({artifact['stats']})", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="world-model-loader")
    ap.add_argument("--check", action="store_true", help="validate only; do not emit")
    ap.add_argument("--reproducible", action="store_true", help="fixed timestamp (determinism)")
    ap.add_argument("--emit-to", type=Path, default=DEFAULT_ARTIFACT)
    args = ap.parse_args(argv)
    return run(check_only=args.check, reproducible=args.reproducible, emit_to=args.emit_to)


if __name__ == "__main__":
    sys.exit(main())
