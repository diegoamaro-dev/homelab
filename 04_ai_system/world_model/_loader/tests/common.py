"""Shared test helpers."""
from __future__ import annotations

from _loader import normalize, parse, registry, resolve
from _loader.cli import ROOT

SRC_ROOT = ROOT


def load_unvalidated(root=ROOT):
    """Run Parse → Resolve → Normalize but NOT Validate (for negative tests)."""
    reg = registry.load(root / "_schema")
    entities, archetypes = parse.parse_tree(root)
    entities = resolve.resolve(entities, archetypes, reg)
    entities = normalize.normalize(entities, reg)
    return entities, archetypes, reg
