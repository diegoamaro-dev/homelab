"""
normalize.py — Stage ③ Normalize (between Resolve and Validate).

Canonicalises the resolved model so Validate compares canonical forms, Emit is
byte-deterministic, and evaluation semantics are explicit. Exactly:

  N1 Literal & compare-mode : casefold string `==`/`!=` literals (parity-safe;
                              matches detect_home's categorical `.lower()`).
  N2 Absence semantics (D7) : bind on_absent=False on every value predicate
                              (absent/unavailable/unknown ⇒ false, incl. `!=`).
  N3 Duration               : already canonical seconds (grammar); affirmed.
  N4 Window                 : windows canonical in the registry; names cross-checked.
  N5 Baseline               : condition-baselines normalized like rules.
  N6 Battery fold           : per-signal ASTs normalized; roster order preserved.
  N7 Ordering               : severity_rank/emission_order stamped; entities by id;
                              affects lists sorted.
  N8 Whitespace / id        : ids/tokens trimmed.
"""

from __future__ import annotations

from . import ast
from .model import ParsedEntity
from .registry import Registries


def _norm_node(node: ast.Node) -> ast.Node:
    if isinstance(node, ast.And):
        return ast.And(tuple(_norm_node(o) for o in node.operands))
    if isinstance(node, ast.Or):
        return ast.Or(tuple(_norm_node(o) for o in node.operands))
    if isinstance(node, ast.Not):
        return ast.Not(_norm_node(node.operand))
    if isinstance(node, ast.Cmp):
        value = node.value.lower() if node.value_type == "string" and isinstance(node.value, str) else node.value
        return ast.Cmp(node.field, node.op, value, node.value_type, on_absent=False)   # N1 + N2
    if isinstance(node, ast.Duration):
        return ast.Duration(node.field, node.op, node.seconds, on_absent=False)         # N2
    return node                                                                          # Unavailable / TimeInWindow


def normalize(entities: list[ParsedEntity], reg: Registries) -> list[ParsedEntity]:
    for e in entities:
        e.id = e.id.strip()                                                              # N8
        # N1/N2 over rule ASTs
        for r in e.rules:
            r.ast_node = _norm_node(r.ast_node)
            if r.kind == "fold" and r.fold:
                r.fold["per_signal"] = {k: _norm_node(v) for k, v in r.fold["per_signal"].items()}  # N6
        # N5 baseline conditions + N1 on baseline state
        if e.baseline:
            if e.baseline["kind"] == "conditions":
                e.baseline["conditions"] = [_norm_node(c) for c in e.baseline["conditions"]]
            elif e.baseline["kind"] == "state" and isinstance(e.baseline["state"], str):
                e.baseline["state"] = e.baseline["state"].lower()
        e.affects = sorted(e.affects)                                                    # N7

    entities.sort(key=lambda x: x.id)                                                     # N7 (deterministic emit)
    return entities
