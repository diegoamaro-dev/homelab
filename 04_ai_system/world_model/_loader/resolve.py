"""
resolve.py — Stage ② Resolve.

Deterministic, idempotent graph construction (no live-state interpretation):
  1. Archetype merge (shallow, one-level).
  2. Aspect expansion — the `battery` roster fold (per-signal dispatch); the
     `firmware` selector stays documentary (no rule).
  3. Reverse-edge derivation — `affects` from `depends_on`.
  4. Registry attach — tier / severity_rank / render_phrase per rule token.
"""

from __future__ import annotations

from . import ast
from .model import ASPECT_SIGNAL_FIELD, ParsedEntity
from .registry import Registries


class ResolveError(ValueError):
    pass


def _disjuncts(node: ast.Node) -> list[ast.Node]:
    return list(node.operands) if isinstance(node, ast.Or) else [node]


def _build_battery_fold(entity: ParsedEntity) -> dict:
    """Turn the battery aspect's OR rule + roster into a per-signal fold."""
    members = entity.fm.get("applies_to")
    if not isinstance(members, list):
        raise ResolveError("battery aspect: applies_to must be a member roster")
    rule = entity.rules[0]
    by_field: dict[str, list[ast.Node]] = {}
    for leaf in _disjuncts(rule.ast_node):
        if not isinstance(leaf, ast.Cmp):
            raise ResolveError(f"battery fold expects Cmp disjuncts, got {leaf!r}")
        by_field.setdefault(leaf.field, []).append(leaf)

    per_signal: dict[str, ast.Node] = {}
    for kind, fld in ASPECT_SIGNAL_FIELD.items():
        leaves = by_field.get(fld, [])
        if not leaves:
            raise ResolveError(f"battery fold: no disjunct for signal kind {kind!r} (field {fld!r})")
        per_signal[kind] = leaves[0] if len(leaves) == 1 else ast.Or(tuple(leaves))

    covered = {m.get("signal") for m in members}
    if not covered <= set(ASPECT_SIGNAL_FIELD):
        raise ResolveError(f"battery roster has unknown signal kinds: {covered - set(ASPECT_SIGNAL_FIELD)}")

    return {
        "members": members,
        "per_signal": per_signal,
        "dedup_key": "device",
        "emit_once": True,
        "render_order": "roster",
    }


def resolve(entities: list[ParsedEntity], archetypes: dict, reg: Registries) -> list[ParsedEntity]:
    # 1. Archetype merge (shallow) + depends_on resolution
    for e in entities:
        arch_id = e.fm.get("archetype")
        depends = list(e.fm.get("depends_on") or [])
        applied: dict = {}
        if arch_id and arch_id in archetypes:
            for k, v in archetypes[arch_id].defaults.items():
                if k not in e.fm:                       # shallow: entity overrides win
                    applied[k] = v
            if not depends and "depends_on" in applied:
                depends = list(applied["depends_on"])
        e.depends_on = depends
        e.archetype_applied = applied

    # 2. Reverse edges: affects[target] = sorted sources that depend on it
    affects: dict[str, list[str]] = {}
    for e in entities:
        for dep in e.depends_on:
            affects.setdefault(dep, [])
            if e.id not in affects[dep]:
                affects[dep].append(e.id)
    for e in entities:
        e.affects = sorted(affects.get(e.id, []))

    # 3. Aspect expansion + 4. registry attach
    for e in entities:
        is_battery_fold = e.kind == "aspect" and isinstance(e.fm.get("applies_to"), list) and e.rules
        for r in e.rules:
            tok = reg.tokens.get(r.token)
            if tok is not None:
                r.tier = tok.tier
                r.severity_rank = tok.severity_rank
                r.render_phrase = tok.render_phrase
        if is_battery_fold:
            r = e.rules[0]
            r.kind = "fold"
            r.fold = _build_battery_fold(e)
            # render prefix, e.g. "[low] low battery: " (names appended by evaluator)
            phrase = r.render_phrase or ""
            r.fold["render_phrase_prefix"] = phrase.split("<", 1)[0]

    return entities
