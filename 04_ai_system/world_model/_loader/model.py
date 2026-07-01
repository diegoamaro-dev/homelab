"""
model.py — enums, field spec and working dataclasses for the resolved model.

The schema enums/constants (frozen §4.3 / schema §2) live here as the single
in-code reference. Entities flow through the pipeline as ParsedEntity objects
carrying their raw frontmatter plus compiled ASTs; emit.py serialises them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Enums (frozen §4.3) ──────────────────────────────────────────────────────
REGIONS = {"infrastructure", "home", "projects", "operator", "self", "environment"}
KINDS = {"device", "service", "pipeline", "project", "person", "self",
         "environment", "aggregate", "aspect"}
STATUSES = {"active", "draft", "retired"}
PRIORITIES = {"critical", "high", "medium", "low"}
BOUNDARIES = {"read_only", "collaboration_context_only"}
BINDING_BACKEND_KEYS = {"ha_entity", "container", "corpus", "probe", "signal"}

REQUIRED_ALWAYS = ("id", "name", "region", "kind", "status", "schema_version")
PROSE_REQUIRED = ("Purpose", "Reasoning")     # "Suggested operator actions" optional (reference/boundary)

# Battery-aspect fold convention: signal kind → the rule field it dispatches on
# (from battery.md's own rule + prose; not invented here).
ASPECT_SIGNAL_FIELD = {"flag": "battery_low", "pct": "battery_level", "categorical": "battery_state"}

_KEBAB = __import__("re").compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SNAKE = __import__("re").compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def is_kebab(s: str) -> bool:
    return bool(_KEBAB.match(s))


def is_snake(s: str) -> bool:
    return bool(_SNAKE.match(s))


def domain_of(entity_id: str) -> str | None:
    """HA entity_id → domain (the text before the first dot), or None."""
    return entity_id.split(".", 1)[0] if "." in entity_id else None


# ── Working structures ───────────────────────────────────────────────────────
@dataclass
class ParsedRule:
    token: str
    condition_source: str
    ast_node: Any                       # ast.Node
    # attached during Resolve/Normalize:
    tier: str | None = None
    severity_rank: int | None = None
    render_phrase: str | None = None
    kind: str = "simple"                # "simple" | "fold"
    fold: dict | None = None            # for kind == "fold"


@dataclass
class ParsedEntity:
    id: str
    file: Path
    region: str
    fm: dict                            # raw frontmatter (bool-safe)
    prose_headings: list[str]
    rules: list[ParsedRule] = field(default_factory=list)
    baseline: dict | None = None        # normalized {kind, ...}
    binding_shape: str | None = None    # "single" | "multi" | None
    binding_signals: dict = field(default_factory=dict)   # name -> backend map
    # resolved:
    depends_on: list[str] = field(default_factory=list)
    affects: list[str] = field(default_factory=list)
    archetype_applied: dict = field(default_factory=dict)

    # convenience accessors on frontmatter
    @property
    def kind(self) -> str:
        return self.fm.get("kind", "")

    @property
    def status(self) -> str:
        return self.fm.get("status", "")

    @property
    def writable(self) -> bool:
        return bool(self.fm.get("writable", False))

    @property
    def collector(self) -> str | None:
        return self.fm.get("collector")

    @property
    def evaluable(self) -> bool:
        return bool(self.rules)


@dataclass
class Archetype:
    archetype_id: str
    defaults: dict
    file: Path
