"""
parse.py — Stage ① Parse.

Read every canonical world_model doc; split YAML frontmatter (the single
authoritative machine surface) from prose; classify entity vs archetype vs
registry/index; compile each condition/baseline into a backend-agnostic AST.

Read-only w.r.t. the docs. Grammar/structural surface errors surface here.

YAML note: PyYAML is YAML 1.1, which parses `off`/`on`/`yes`/`no` as booleans.
We use a strict loader that resolves ONLY `true`/`false` as bool, so baseline
states like `{ state: off }` stay the string "off" (never False).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from . import ast, grammar
from .model import Archetype, ParsedEntity, ParsedRule


class ParseError(ValueError):
    pass


# ── Bool-safe YAML loader (true/false only) ──────────────────────────────────
class _WMLoader(yaml.SafeLoader):
    pass


for _ch in "yYnNoOtTfF":
    if _ch in _WMLoader.yaml_implicit_resolvers:
        _WMLoader.yaml_implicit_resolvers[_ch] = [
            (tag, rx) for (tag, rx) in _WMLoader.yaml_implicit_resolvers[_ch]
            if tag != "tag:yaml.org,2002:bool"
        ]
_WMLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"),
    list("tTfF"),
)

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

# Files under world_model/ that are NOT entities.
_NON_ENTITY_NAMES = {"README.md", "entity.schema.md", "tokens.md", "windows.md", "collectors.md"}


def _split(text: str, path: Path) -> tuple[dict, str]:
    m = _FRONTMATTER.match(text)
    if not m:
        raise ParseError(f"{path}: missing YAML frontmatter")
    try:
        fm = yaml.load(m.group(1), Loader=_WMLoader)
    except yaml.YAMLError as exc:
        raise ParseError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(fm, dict):
        raise ParseError(f"{path}: frontmatter is not a mapping")
    return fm, m.group(2)


def _binding(fm: dict) -> tuple[str | None, dict]:
    b = fm.get("binding")
    if b is None:
        return None, {}
    if not isinstance(b, dict):
        raise ParseError(f"binding must be a map, got {type(b).__name__}")
    from .model import BINDING_BACKEND_KEYS
    if BINDING_BACKEND_KEYS & set(b):                 # single-signal
        return "single", {"state": b}
    return "multi", dict(b)                           # named multi-signal


def _compile_conditions(fm: dict, path: Path) -> tuple[list[ParsedRule], dict | None]:
    rules: list[ParsedRule] = []
    for r in fm.get("anomaly_rules", []) or []:
        if "token" not in r or "condition" not in r:
            raise ParseError(f"{path}: anomaly rule missing token/condition: {r!r}")
        try:
            node = grammar.parse(r["condition"])
        except grammar.GrammarError as exc:
            raise ParseError(f"{path}: rule {r['token']!r}: {exc}") from exc
        rules.append(ParsedRule(token=r["token"], condition_source=r["condition"], ast_node=node))

    baseline = None
    b = fm.get("baseline")
    if isinstance(b, dict):
        if "state" in b:
            baseline = {"kind": "state", "state": b["state"]}
        elif "schedule" in b:
            baseline = {"kind": "schedule", "schedule": b["schedule"]}
        elif "conditions" in b:
            conds = []
            for c in b["conditions"]:
                try:
                    conds.append(grammar.parse(c))
                except grammar.GrammarError as exc:
                    raise ParseError(f"{path}: baseline {c!r}: {exc}") from exc
            baseline = {"kind": "conditions", "conditions": conds, "sources": list(b["conditions"])}
    return rules, baseline


def parse_entity(path: Path, region: str) -> ParsedEntity:
    fm, body = _split(path.read_text(encoding="utf-8"), path)
    headings = _HEADING.findall(body)
    shape, signals = _binding(fm)
    rules, baseline = _compile_conditions(fm, path)
    ent = ParsedEntity(
        id=str(fm.get("id", "")),
        file=path,
        region=region,
        fm=fm,
        prose_headings=headings,
        rules=rules,
        baseline=baseline,
        binding_shape=shape,
        binding_signals=signals,
    )
    return ent


def parse_archetype(path: Path) -> Archetype:
    fm, _ = _split(path.read_text(encoding="utf-8"), path)
    if "archetype" not in fm:
        raise ParseError(f"{path}: archetype file missing 'archetype' id")
    return Archetype(archetype_id=str(fm["archetype"]), defaults=dict(fm.get("defaults", {})), file=path)


def parse_tree(root: Path) -> tuple[list[ParsedEntity], dict[str, Archetype]]:
    """Return (entities, archetypes) discovered under world_model/."""
    entities: list[ParsedEntity] = []
    archetypes: dict[str, Archetype] = {}

    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root)
        parts = rel.parts
        if parts[0] == "_loader":
            continue                                   # the loader package itself
        if parts[0] == "_schema":
            if len(parts) >= 2 and parts[1] == "archetypes":
                a = parse_archetype(md)
                archetypes[a.archetype_id] = a
            continue                                   # registries/schema handled elsewhere
        if md.name in _NON_ENTITY_NAMES or len(parts) < 2:
            continue                                   # index/schema docs, not entities
        region = parts[0]
        entities.append(parse_entity(md, region))

    if not entities:
        raise ParseError(f"no entities found under {root}")
    return entities, archetypes
